from django.conf.urls import patterns, url
from checkout.views import checkout_as_guest, checkout

urlpatterns = patterns('',
                       url(r'^$', checkout, name="checkout"),
                       url(r'^guest/$', checkout_as_guest, name="guest_checkout")
                       )
