from django.conf.urls import patterns, url
from wishlists.views import create_wishlist, view_wishlist

urlpatterns = patterns('',
                    url(r'^create$', create_wishlist, name="wishlist_create"),
                    url(r'^view/(\d+)$', view_wishlist, name="wishlist_view"),
)