from django.conf.urls import patterns, url
from orders.views import detail_view, cancel_view, receipt_view

urlpatterns = patterns('',
                    url(r'^detail/(?P<order_id>\d+)$', detail_view, name="order_detail"),
                    url(r'^cancel/(?P<order_id>\d+)$', cancel_view, name="order_cancel"),
                    url(r'^receipt/(?P<order_id>\d+)$', receipt_view, name="order_receipt")
)
