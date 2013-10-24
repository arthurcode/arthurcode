from django.conf.urls import patterns, url
from giftcards.views import home_view, check_balance_view


urlpatterns = patterns('',
                       url(r'^$', home_view, name='gc_home'),
                       url(r'^check-balance$', check_balance_view, name='gc_check_balance'),
)