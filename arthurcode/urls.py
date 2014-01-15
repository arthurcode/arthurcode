from django.conf.urls import patterns, include, url
import blog.urls
import catalogue.urls
import cart.urls
from catalogue.views import home_view
import checkout.urls
import accounts.urls
import search.urls
import reviews.urls
import questions.urls
import orders.urls
import wishlists.urls
import giftcards.urls
import emaillist.urls
from arthurcode.views import AboutView, ContactView, FAQView

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

    url(r'^about/', AboutView.as_view(), name="about"),

    url(r'^contact/', ContactView.as_view(), name="contact"),

    url(r'^faq/', FAQView.as_view(), name="faq"),

    url(r'^blog/', include(blog.urls)),

    url(r'^products/', include(catalogue.urls)),

    url(r'^$', home_view, name="home"),

    url(r'^cart/', include(cart.urls)),

    url(r'^checkout/', include(checkout.urls)),

    url(r'^accounts/', include(accounts.urls)),

    url(r'^search/', include(search.urls)),

    url(r'^reviews/', include(reviews.urls)),

    url(r'^questions/', include(questions.urls)),

    url(r'orders/', include(orders.urls)),

    url(r'wishlists/', include(wishlists.urls)),

    url(r'giftcards/', include(giftcards.urls)),

    url(r'mailing-list/', include(emaillist.urls)),
)
