from django.conf.urls import patterns, url
from cart.views import show_cart, cart_summary, add_product_to_cart


urlpatterns = patterns('',
                       url(r'^$', show_cart, name='show_cart'),
                       url(r'^ajax_summary$', cart_summary, name="ajax_cart_summary"),
                       url(r'^add-product-to-cart', add_product_to_cart, name="ajax_add_product_to_cart"),
)
