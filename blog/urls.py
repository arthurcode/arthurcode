__author__ = 'rhyanarthur'

from django.conf.urls import patterns, url, include
from blog.views import BlogYearArchiveView, BlogMonthArchiveView, BlogDayArchiveView, BlogArchiveView, \
    BlogPostDetailView, index
from django.views.generic import TemplateView

urlpatterns = patterns('',

                       url(r'^$',
                           index,
                           name="index"),

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
                           name="day_archive"),

                       url(r'^(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[-\w]+)',
                           BlogPostDetailView.as_view(),
                           name="post_detail"),
)

urlpatterns += patterns('',
    (r'^comments/', include('django.contrib.comments.urls')),
    url(r'^about/', TemplateView.as_view(template_name="blog/about.html"), name="about"),
    url(r'^contact/', TemplateView.as_view(template_name="blog/contact.html"), name="contact"),
)