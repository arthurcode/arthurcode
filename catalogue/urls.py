from django.conf.urls import patterns, url
from catalogue.views import product_detail_view, category_view, featured_view, restock_notify_view, brands_view, \
    brand_view

urlpatterns = patterns('',
                        url(r'^brands$', brands_view, name="brands"),
                        url(r'^brands/(?P<brand_slug>[-\w]*)$', brand_view, name="brand"),
                        url(r'^detail/(?P<slug>[-\w]+)$', product_detail_view, name="catalogue_product"),
                        url(r'^featured', featured_view, name="catalogue_featured"),
                        url(r'^(?P<category_slug>[-\w]*)$', category_view, name="catalogue_category"),
                        url(r'^restock-notify/(\d+)$', restock_notify_view, name="restock_notify"),


)
