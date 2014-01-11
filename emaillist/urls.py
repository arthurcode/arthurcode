from django.conf.urls import patterns, url
from emaillist.views import subscribe, subscribe_complete, unsubscribe, unsubscribe_user, unsubscribe_complete

urlpatterns = patterns('',
                       url(r'^subscribe/$', subscribe, name="subscribe"),
                       url(r'^subscribe-complete/$', subscribe_complete, name="subscribe_complete"),
                       url(r'^unsubscribe$', unsubscribe_user, name="unsubscribe_user"),
                       url(r'^unsubscribe/(\S+)$', unsubscribe, name="unsubscribe"),
                       url(r'^unsubscribe-complete/$', unsubscribe_complete, name="unsubscribe_complete"),
                       )