from django.conf.urls import patterns, include, url
import blog.urls
import catalogue.urls
import cart.urls
from catalogue.views import home_view
import checkout.urls
import accounts.urls
import lazysignup.urls

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'arthurcode.views.home', name='home'),
    # url(r'^arthurcode/', include('arthurcode.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^blog/', include(blog.urls)),

    url(r'^products/', include(catalogue.urls)),

    url(r'^$', home_view, name="home"),

    url(r'^cart/', include(cart.urls)),

    url(r'^checkout/', include(checkout.urls)),

    url(r'^accounts/', include(accounts.urls)),

    url(r'^convert/', include(lazysignup.urls)),
)
