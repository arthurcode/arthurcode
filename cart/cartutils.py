from cart.models import CartItem, ProductCartItem, GiftCardCartItem
from django.shortcuts import get_object_or_404
import decimal
from exceptions import ValueError

CART_ID_SESSION_KEY = 'cart_id'


# get the current user's cart id, sets new one if blank
def _cart_id(request):
    if request.session.get(CART_ID_SESSION_KEY, '') == '':
        request.session[CART_ID_SESSION_KEY] = CartItem.generate_cart_id()
    return request.session[CART_ID_SESSION_KEY]


def get_cart_items(request):
    return list(get_cart_products(request)) + list(get_cart_gift_cards(request))


def get_cart_products(request):
    """
    Returns the subset of items in the cart that are linked to products (as opposed to gift certificates).
    The instances are of model class ProductCartItem
    """
    return ProductCartItem.objects.filter(cart_id=_cart_id(request))


def get_cart_gift_cards(request):
    return GiftCardCartItem.objects.filter(cart_id=_cart_id(request))


# add a product instance to the customer's cart
def add_to_cart(request, product_instance, quantity):
    # this shouldn't happen because the form has been validated, but just in case ...
    if quantity < 1:
        return

    # get products in cart
    cart_products = get_cart_products(request)

    # check to see if item is already in cart
    for cart_item in cart_products:
        if cart_item.item.id == product_instance.id:
            cart_item.augment_quantity(quantity)
            return cart_item

    # create and save a new cart item
    ci = ProductCartItem()
    ci.item = product_instance
    ci.quantity = quantity
    ci.cart_id = _cart_id(request)
    ci.full_clean()
    ci.save()
    return ci


def add_gift_card_to_cart(request, value, quantity):
    gcs = get_cart_gift_cards(request)
    for gc in gcs:
        if gc.value == value:
            gc.augment_quantity(quantity)
            return gc
    gc = GiftCardCartItem()
    gc.value = value
    gc.quantity = quantity
    gc.cart_id = _cart_id(request)
    gc.full_clean()
    gc.save()
    return gc


# returns the total number of items in the user's cart:
def cart_distinct_item_count(request):
    count = 0
    for ci in get_cart_items(request):
        count += ci.quantity
    return count


def get_single_item(request, item_id):
    return as_base_item(get_object_or_404(CartItem, id=item_id, cart_id=_cart_id(request)))


def get_item_for_product(request, item):
    """
    Returns the cart-item corresponding to the given product, if one exists.  Returns None if the product is not
    yet in the cart.
    """
    items = get_cart_products(request).filter(item_id=item.id)
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
        # this should also delete any linked WishListToCartItem links
        cart_item.delete()


def cart_subtotal(request):
    cart_total = decimal.Decimal('0.00')
    cart_items = get_cart_items(request)
    for cart_item in cart_items:
        cart_total += cart_item.total()
    return cart_total


def clear_cart(request):
    for item in get_cart_items(request):
        item.delete()


def get_base_item(id):
    """
    Returns the ProductCartItem object with the given id.  Will no return an instance of CartItem, since this is
    too generic of a model to be useful in most cases.
    """
    cart_item = CartItem.objects.get(id=id)
    return as_base_item(cart_item)

def as_base_item(cart_item):
    """
    Cast a generic CartItem to an instance of ProductCartItem.
    """
    if isinstance(cart_item, (ProductCartItem, GiftCardCartItem)):
        return cart_item
    try:
        return cart_item.productcartitem
    except ProductCartItem.DoesNotExist:
        return cart_item.giftcardcartitem