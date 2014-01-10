from django.conf.urls import patterns, url
from emaillist.views import subscribe, subscribe_complete

urlpatterns = patterns('',
                       url(r'^subscribe/$', subscribe, name="subscribe"),
                       url(r'^subscribe-complete/$', subscribe_complete, name="subscribe_complete"),
                       )