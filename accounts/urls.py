from django.conf.urls import patterns, url
from accounts.views import login_or_create_account, view_orders, view_personal, view_wishlists, view_reviews,\
    create_public_profile
from django.contrib.auth.views import logout

urlpatterns = patterns('',
                       url(r'^login/$', login_or_create_account, name="login_or_create_account"),
                       url(r'^logout/$', logout, name="logout"),
                       url(r'^create-public-profile', create_public_profile, name="create_public_profile"),
                       url(r'^orders/$', view_orders, name="account_orders"),
                       url(r'^personal/$', view_personal, name="account_personal"),
                       url(r'^wishlists/$', view_wishlists, name="account_wishlists"),
                       url(r'^reviews/$', view_reviews, name="account_reviews"),
                       )

