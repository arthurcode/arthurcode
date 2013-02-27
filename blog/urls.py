__author__ = 'rhyanarthur'

from django.conf.urls import patterns, url
from django.views.generic.dates import ArchiveIndexView
from blog.models import Post
from blog.views import BlogYearArchiveView, BlogMonthArchiveView, BlogDayArchiveView


urlpatterns = patterns('',
                       url(r'^archive/$',
                           ArchiveIndexView.as_view(model=Post, date_field="pub_date"),
                           name="archive"),

                       url(r'^(?P<year>\d{4})/$',
                           BlogYearArchiveView.as_view(),
                           name="year_archive"),

                       url(r'^(?P<year>\d{4})/(?P<month>\d+)/$',
                           BlogMonthArchiveView.as_view(month_format='%m'),
                           name="month_archive"),

                       url(r'^(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/$',
                           BlogDayArchiveView.as_view(month_format='%m'),
                           name="day_archive")
)