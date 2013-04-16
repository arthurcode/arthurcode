from django.shortcuts import render_to_response
from django.template import RequestContext
from cart import cartutils


def show_cart(request):
    if request.method == "POST":
        postdata = request.POST.copy()
        if 'Remove' in postdata:
            cartutils.remove_from_cart(request)
        if 'Update' in postdata:
            cartutils.update_cart(request)
        if 'Checkout' in postdata:
            pass
    cart_items = cartutils.get_cart_items(request)
    cart_subtotal = cartutils.cart_subtotal(request)
    return render_to_response('cart.html', locals(), context_instance=RequestContext(request))