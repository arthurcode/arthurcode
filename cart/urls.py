from django.conf.urls import patterns, url
from cart.views import show_cart


urlpatterns = patterns('',
                       url(r'^$', show_cart, name='show_cart'),
)
