from cart import cartutils


def annotate_is_in_cart(request, wish_items):
    """
    Annotates an 'in_cart' attribute to each WishListItem in the list.  Will be 'True' if the wish list item is in the
    customer's cart and False otherwise.
    """
    cart_items = cartutils.get_cart_items(request)
    in_cart = wish_items.filter(cart_links__cart_item__in=cart_items)

    for wish_item in wish_items:
        setattr(wish_item, 'in_cart', wish_item in in_cart)
