from django.conf.urls import patterns, url
from catalogue.views import product_detail_view, category_view, featured_view, restock_notify_view

urlpatterns = patterns('',
                        url(r'^detail/(?P<slug>[-\w]+)$', product_detail_view, name="catalogue_product"),
                        url(r'^featured', featured_view, name="catalogue_featured"),
                        url(r'^(?P<category_slug>[-\w]*)$', category_view, name="catalogue_category"),
                        url(r'^restock-notify/(\d+)$', restock_notify_view, name="restock_notify"),
)
