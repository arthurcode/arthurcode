from django.conf.urls import patterns, url
from checkout.views import checkout, contact_info, shipping_info, billing_info, review, cancel

urlpatterns = patterns('',
                       url(r'^$', checkout, name="checkout"),
                       url(r'^contact/$', contact_info, name="contact"),
                       url(r'^shipping/$', shipping_info, name="shipping"),
                       url(r'^billing/$', billing_info, name="billing"),
                       url(r'^review/$', review, name="review"),
                       url(r'^cancel/$', cancel, name="cancel"),
                       )
