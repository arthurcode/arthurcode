from django.conf.urls import patterns, url
from catalogue.views import product_detail_view

urlpatterns = patterns('',
                        url(r'^detail/(?P<slug>[-\w]+)$', product_detail_view, name="catalogue_product"),
)
