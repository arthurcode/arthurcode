from django.conf.urls import patterns, url
from accounts.views import login_or_create_account, show_account
from django.contrib.auth.views import logout

urlpatterns = patterns('',
                       url(r'^login/$', login_or_create_account, name="login_or_create_account"),
                       url(r'^logout/$', logout, name="logout"),
                       url(r'^my_account/$', show_account, name="show_account"),
                       )

