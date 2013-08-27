from django.conf.urls import patterns, url
from checkout.views import checkout, contact_info, shipping_info, billing_info, review, cancel, create_account

urlpatterns = patterns('',
                       url(r'^$', checkout, name="checkout"),
                       url(r'^contact/$', contact_info, name="checkout_contact"),
                       url(r'^shipping/$', shipping_info, name="checkout_shipping"),
                       url(r'^billing/$', billing_info, name="checkout_billing"),
                       url(r'^review/$', review, name="checkout_review"),
                       url(r'^create-account/$', create_account, name="checkout_create_account"),
                       url(r'^cancel/$', cancel, name="checkout_cancel"),
                       )
