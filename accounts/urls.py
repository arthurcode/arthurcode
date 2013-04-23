from django.conf.urls import patterns, url
from accounts.views import login_or_create_account, show_account

urlpatterns = patterns('',
                       url(r'^login/$', login_or_create_account, name="login_or_create_account"),
                       url(r'^my_account/$', show_account, name="show_account"),
                       )

