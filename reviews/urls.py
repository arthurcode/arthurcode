from django.conf.urls import patterns, url
from reviews.views import review_view

urlpatterns = patterns('',
                    url(r'^(?P<product_slug>[-\w]*)$', review_view, name="product_review")
)
