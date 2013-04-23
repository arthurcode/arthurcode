from django.conf.urls import patterns, url
from checkout.views import choose_checkout_method, checkout_as_guest, checkout_account

urlpatterns = patterns('',
                       url(r'^$', choose_checkout_method, name="checkout_home"),
                       url(r'^guest/$', checkout_as_guest, name="guest_checkout"),
                       url(r'^account/$', checkout_account, name="account_checkout"),
                       )
