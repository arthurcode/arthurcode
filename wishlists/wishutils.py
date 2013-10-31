from cart import cartutils
from models import WishListItemToCartItem, WishList


def add_wishlist_item_to_cart(request, wishlist_item):
    product_instance = wishlist_item.instance
    cart_item = cartutils.add_to_cart(request, product_instance, 1)
    # link the wish list item to the cart item
    link = WishListItemToCartItem(
        wishlist_item=wishlist_item,
        cart_item=cart_item,
    )
    link.full_clean()
    link.save()


def get_wishlists(request):
    # returns a list of wish lists that the user has been shopping from
    cart_id = cartutils._cart_id(request)
    wishlist_item_ids = WishListItemToCartItem.objects.filter(cart_item__cart_id=cart_id).values_list('wishlist_item')
    return WishList.objects.filter(items__id__in=wishlist_item_ids).distinct()


def get_wishlists_for_item(cart_item):
    wishlist_item_ids = cart_item.wishlist_links.values_list('wishlist_item')
    return WishList.objects.filter(items__id__in=wishlist_item_ids).distinct()
