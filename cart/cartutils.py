from cart.models import CartItem
from catalogue.models import Product
from django.shortcuts import get_object_or_404
import decimal
from exceptions import ValueError

CART_ID_SESSION_KEY = 'cart_id'


# get the current user's cart id, sets new one if blank
def _cart_id(request):
    if request.session.get(CART_ID_SESSION_KEY, '') == '':
        request.session[CART_ID_SESSION_KEY] = CartItem.generate_cart_id()
    return request.session[CART_ID_SESSION_KEY]


# return all items from the current user's cart
def get_cart_items(request):
    return CartItem.objects.filter(cart_id=_cart_id(request))


# add a product instance to the customer's cart
def add_to_cart(request, product_instance, quantity):
    # this shouldn't happen because the form has been validated, but just in case ...
    if quantity < 1:
        return

    # get products in cart
    cart_items = get_cart_items(request)
    item_in_cart = False
    # check to see if item is already in cart
    for cart_item in cart_items:
        if cart_item.item.id == product_instance.id:
            cart_item.augment_quantity(quantity)
            item_in_cart = True
    if not item_in_cart:
        # create and save a new cart item
        ci = CartItem()
        ci.item = product_instance
        ci.quantity = quantity
        ci.cart_id = _cart_id(request)
        ci.save()


# returns the total number of items in the user's cart:
def cart_distinct_item_count(request):
    return get_cart_items(request).count()

def get_single_item(request, item_id):
    return get_object_or_404(CartItem, id=item_id, cart_id=_cart_id(request))


def get_item_for_product(request, item):
    """
    Returns the cart-item corresponding to the given product, if one exists.  Returns None if the product is not
    yet in the cart.
    """
    items = get_cart_items(request).filter(item_id=item.id)
    if not items:
        return None
    return items[0]


def update_cart(request):
    postdata = request.POST.copy()
    item_id = postdata['item_id']
    quantity = postdata['quantity']
    cart_item = get_single_item(request, item_id)
    if cart_item:
        try:
            if int(quantity) > 0:
                cart_item.quantity = int(quantity)
                cart_item.save()
            else:
                remove_from_cart(request)
        except ValueError:
            # user gave an invalid quantity string, do nothing.
            pass


def remove_from_cart(request):
    postdata = request.POST.copy()
    item_id = postdata['item_id']
    cart_item = get_single_item(request, item_id)
    if cart_item:
        cart_item.delete()


def cart_subtotal(request):
    cart_total = decimal.Decimal('0.00')
    cart_products = get_cart_items(request)
    for cart_item in cart_products:
        cart_total += cart_item.total()
    return cart_total


def clear_cart(request):
    for item in get_cart_items(request):
        item.delete()