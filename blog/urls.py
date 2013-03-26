__author__ = 'rhyanarthur'

from django.conf.urls import patterns, url, include
from blog.views import BlogYearArchiveView, BlogMonthArchiveView, BlogDayArchiveView, BlogArchiveView, \
    BlogPostDetailView, index, AboutView, ContactView, FeedsView, BlogDraftPostDetailView
from blog.feeds import LatestPostsFeed, AtomLatestPostsFeed

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

                       url(r'^drafts/(?P<year>\d{4})/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>[-\w]+)',
                           BlogDraftPostDetailView.as_view(),
                           name="draft_post_detail"),
)

urlpatterns += patterns('',
    (r'^comments/', include('comments.urls')),
    url(r'^about/', AboutView.as_view(), name="about"),
    url(r'^contact/', ContactView.as_view(), name="contact"),
    url(r'^rss/', LatestPostsFeed(), name="rss"),
    url(r'atom/', AtomLatestPostsFeed(), name="atom"),
    url(r'feeds/', FeedsView.as_view(), name="feeds"),
)