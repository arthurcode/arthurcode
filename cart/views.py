from django.shortcuts import render_to_response
from django.template import RequestContext
from cart import cartutils
from django.core.urlresolvers import reverse
from urlparse import urlparse
from cart.forms import UpdateCartItemForm


def show_cart(request):
    bound_form = None
    bound_form_id = None
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
            pass
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
    continue_shopping_url = reverse('catalogue_category', kwargs={'category_slug': ''})
    last_url = request.META.get('HTTP_REFERER', None)  # (sic)

    if last_url:
        pr = urlparse(last_url)
        path = pr[2]
        if path.startswith(continue_shopping_url):
            continue_shopping_url = path
            query = pr[4]
            if query:
                continue_shopping_url += "?%s" % query
    return continue_shopping_url