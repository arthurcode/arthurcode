from django.conf.urls import patterns, url
from checkout.views import checkout, contact_info, shipping_info, billing_info, review, cancel, create_account, \
    redeem_gift_card, shipping_method

urlpatterns = patterns('',
                       url(r'^$', checkout, name="checkout"),
                       url(r'^contact/$', contact_info, name="checkout_contact"),
                       url(r'^shipping/$', shipping_info, name="checkout_shipping"),
                       url(r'^shipping-method/$', shipping_method, name="checkout_shipping_method"),
                       url(r'^billing/$', billing_info, name="checkout_billing"),
                       url(r'^review/$', review, name="checkout_review"),
                       url(r'^create-account/$', create_account, name="checkout_create_account"),
                       url(r'^cancel/$', cancel, name="checkout_cancel"),
                       url(r'^redeem-gift-card$', redeem_gift_card, name="ajax_redeem_gift_card"),
                       )
