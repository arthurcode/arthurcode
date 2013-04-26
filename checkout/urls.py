from django.conf.urls import patterns, url
from checkout.views import checkout
from checkout.forms import OrderWizard

urlpatterns = patterns('',
                       url(r'^$', checkout, name="checkout"),
                       url(r'^guest/$', OrderWizard.as_view(OrderWizard.FORMS), name="guest_checkout")
                       )
