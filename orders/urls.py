from django.conf.urls import patterns, url
from orders.views import detail_view

urlpatterns = patterns('',
                    url(r'^detail/(?P<order_id>\d+)$', detail_view, name="order_detail"),
)
