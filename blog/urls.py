__author__ = 'rhyanarthur'

from django.conf.urls import patterns, url
from blog.views import BlogYearArchiveView, BlogMonthArchiveView, BlogDayArchiveView, BlogArchiveView


urlpatterns = patterns('',
                       url(r'^archive/$',
                           BlogArchiveView.as_view(),
                           name="archive"),

                       url(r'^(?P<year>\d{4})/$',
                           BlogYearArchiveView.as_view(),
                           name="year_archive"),

                       url(r'^(?P<year>\d{4})/(?P<month>\d+)/$',
                           BlogMonthArchiveView.as_view(),
                           name="month_archive"),

                       url(r'^(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
                           BlogDayArchiveView.as_view(),
                           name="day_archive")
)