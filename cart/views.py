from django.shortcuts import render_to_response
from django.template import RequestContext
from cart import cartutils
from django.core.urlresolvers import reverse
from urlparse import urlparse
from cart.forms import UpdateCartItemForm
from django.utils.http import is_safe_url
from django.http import HttpResponseRedirect


def show_cart(request):
    bound_form = None
    bound_form_id = None
    cart_items = None
    if request.method == "POST":
        postdata = request.POST.copy()
        if 'Remove' in postdata:
            cartutils.remove_from_cart(request)
        if 'Update' in postdata:
            update_form = UpdateCartItemForm(request, postdata)
            if update_form.is_valid():
                cartutils.update_cart(request)
            else:
                bound_form = update_form
                try:
                    bound_form_id = int(postdata.get('item_id', None))
                except ValueError:
                    bound_form_id = -1
        if 'Checkout' in postdata:
            # do a stock check before allowing the user to start the checkout process
            # TODO: do this stock check everytime in the view
            cart_items = cartutils.get_cart_items(request)
            checkout_errors = []
            for cart_item in cart_items:
                error = cart_item.check_stock()
                if error:
                    checkout_errors.append("%s: %s" % (unicode(cart_item), error))
            if not checkout_errors:
                return HttpResponseRedirect(reverse('checkout'))

    if not cart_items:
        cart_items = cartutils.get_cart_items(request)

    for cart_item in cart_items:
        if bound_form_id == cart_item.id:
            form = bound_form
        else:
            # create an unbound form
            form = UpdateCartItemForm(request)
            form.fields['item_id'].widget.attrs['value'] = cart_item.id
        setattr(cart_item, 'update_form', form)
    cart_subtotal = cartutils.cart_subtotal(request)
    continue_shopping_url = get_continue_shopping_url(request)
    return render_to_response('cart.html', locals(), context_instance=RequestContext(request))


def get_continue_shopping_url(request):
    """
    Returns a url that can be used in a 'continue-shopping' link from the shopping cart page.  By default the method
    will return the root products url: /products/.  The referrer url will be used iff it extends from /products/.  Any
    get query parameters in the referrer url will be preserved if it is used.
    """
    default_continue_shopping_url = reverse('catalogue_category', kwargs={'category_slug': ''})
    last_url = request.META.get('HTTP_REFERER', None)  # (sic)
    # Ensure the user-originating redirection url is safe.
    if not is_safe_url(url=last_url, host=request.get_host()):
        return default_continue_shopping_url

    if last_url:
        pr = urlparse(last_url)
        path = pr[2]
        if path.startswith(default_continue_shopping_url):
            return last_url
    return default_continue_shopping_url