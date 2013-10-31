from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from cart import cartutils
from wishlists import wishutils
from django.core.urlresolvers import reverse
from urlparse import urlparse
from cart.forms import UpdateCartItemForm, ProductAddToCartForm
from django.utils.http import is_safe_url
from django.http import HttpResponseRedirect
from catalogue.models import ProductInstance, Product
import logging
from utils.decorators import ajax_required
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def show_cart(request):
    """
    Show the cart contents on a GET request.  On POST, check if the user is trying to update/remove items from their
    cart, or if they are trying to checkout.
    """
    bound_form = None
    bound_form_id = None
    checkout_errors = None

    if request.method == "POST":
        postdata = request.POST.copy()
        if 'Remove' in postdata:
            cartutils.remove_from_cart(request)
        if 'Update' in postdata:
            bound_form, bound_form_id = _process_update_cart_form(request, postdata)
        if 'Checkout' in postdata:
            # do a stock check before allowing the user to start the checkout process
            checkout_errors = _get_cart_errors(request)
            if not checkout_errors:
                checkout_url = reverse('checkout')
                return HttpResponseRedirect(checkout_url)

    try:
        cart_items = cartutils.get_cart_items(request)

        if checkout_errors == None:
            checkout_errors = _get_cart_errors(request)

        for cart_item in cart_items:
            if bound_form_id == cart_item.id:
                form = bound_form
            else:
                # create an unbound form
                form = UpdateCartItemForm(request)
                form.fields['item_id'].widget.attrs['value'] = cart_item.id
            setattr(cart_item, 'update_form', form)
            setattr(cart_item, 'wishlists', wishutils.get_wishlists_for_item(cart_item))

        cart_subtotal = cartutils.cart_subtotal(request)
        continue_shopping_url = get_continue_shopping_url(request)

        context = {
            'cart_subtotal': cart_subtotal,
            'continue_shopping_url': continue_shopping_url,
            'cart_items': cart_items,
            'checkout_errors': checkout_errors,
            'wishlists': wishutils.get_wishlists(request),
        }

        return render_to_response('cart.html', context, context_instance=RequestContext(request))
    except ProductInstance.DoesNotExist:
        # something funny is happened - the user has an item in his cart that for some reason no longer exists in our
        # system.  This should never happen, but I guess you never know.
        logger.exception("Unknown product instance in cart")
        cartutils.clear_cart(request)
        return HttpResponseRedirect(reverse('show_cart'))


def get_continue_shopping_url(request):
    """
    Returns a url that can be used in a 'continue-shopping' link from the shopping cart page.  By default the method
    will return the root products url: /products/.  The referrer url will be used iff it extends from /products/ or
    /wishlists/shop.  Any get query parameters in the referrer url will be preserved if it is used.
    """
    default_continue_shopping_url = reverse('catalogue_category', kwargs={'category_slug': ''})
    last_url = request.META.get('HTTP_REFERER', None)  # (sic)
    # Ensure the user-originating redirection url is safe.
    if not is_safe_url(url=last_url, host=request.get_host()):
        return default_continue_shopping_url

    if last_url:
        pr = urlparse(last_url)
        path = pr[2]
        if path.startswith(default_continue_shopping_url) or path.startswith('/wishlists/shop/'):
            return last_url
    return default_continue_shopping_url


def _process_update_cart_form(request, postdata):
    """
    Checks if the update cart item form is valid, and if so calls cartutils.update_cart().  If there are errors
    the method returns the bound form instance and the id of the cart-item it is associated with.
    """
    update_form = UpdateCartItemForm(request, postdata)
    if update_form.is_valid():
        cartutils.update_cart(request)
        return None, None
    else:
        bound_form = update_form
        try:
            bound_form_id = int(postdata.get('item_id', None))
        except ValueError:
            bound_form_id = -1
        return bound_form, bound_form_id


def _get_cart_errors(request):
    """
    Checks this cart for any stock errors (ie. if there are more items in this user's cart that we have in stock)
    Returns an empty list if there are no errors.
    """
    checkout_errors = []
    cart_items = cartutils.get_cart_items(request)
    for cart_item in cart_items:
        error = cart_item.check_stock()
        if error:
            checkout_errors.append("%s: %s" % (unicode(cart_item), error))
    return checkout_errors


@ajax_required
def cart_summary(request):
    """
    Returns a cart summary html snippet that can be used for refreshing the cart-summary div via ajax.
    """
    template = "_cart_summary.html"
    context = {
        'cart_item_count': cartutils.cart_distinct_item_count(request)
    }
    return render_to_response(template, context, context_instance=RequestContext(request))


@ajax_required
@require_POST
def add_product_to_cart(request):
    data = request.POST.copy()
    product_id = data.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    form = ProductAddToCartForm(product, request, data=data)

    if form.is_valid():
        form.add_to_cart()
        context = {
            'instance': form.get_product_instance(form.cleaned_data),
            'items_in_cart': cartutils.cart_distinct_item_count(request),
            'subtotal': cartutils.cart_subtotal(request),
            'quantity': form.cleaned_data.get('quantity', None),
        }
        return render_to_response('post_add_to_cart_summary.html', context, context_instance=RequestContext(request))
    else:
        raise Exception("Error in add-to-cart form submitted via ajax")