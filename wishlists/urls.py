from django.conf.urls import patterns, url
from wishlists.views import create_wishlist, view_wishlist, edit_wishlist, shop_wishlist, delete_wishlist, add_wish_list_item_to_cart

urlpatterns = patterns('',
                    url(r'^create$', create_wishlist, name="wishlist_create"),
                    url(r'^view/(\d+)$', view_wishlist, name="wishlist_view"),
                    url(r'^edit/(\d+)$', edit_wishlist, name="wishlist_edit"),
                    url(r'^shop/(.+)$', shop_wishlist, name="wishlist_shop"),
                    url(r'^delete/(\d+)$', delete_wishlist, name="wishlist_delete"),
                    url(r'^add-item-to-cart$', add_wish_list_item_to_cart, name="ajax_add_wishlist_item_to_cart")
)