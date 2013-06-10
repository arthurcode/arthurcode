from django.conf.urls import patterns, url
from search.views import product_search_view

urlpatterns = patterns('',
                        url(r'^products$', product_search_view, name="product_search"),
                        )
