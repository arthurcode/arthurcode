from django.conf.urls import patterns, url
from catalogue.views import product_detail_view, category_view, featured_view, review_view

urlpatterns = patterns('',
                        url(r'^detail/(?P<slug>[-\w]+)$', product_detail_view, name="catalogue_product"),
                        url(r'^featured', featured_view, name="catalogue_featured"),
                        url(r'^(?P<category_slug>[-\w]*)$', category_view, name="catalogue_category"),
                        url(r'^review/(?P<slug>[-\w]+)$', review_view, name="product_review")
)
