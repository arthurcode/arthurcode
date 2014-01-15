from blog.models import Post
from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView, ArchiveIndexView, DateDetailView
from django.views.generic.base import TemplateView
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response
from django.template import RequestContext
import collections
import datetime
from feeds import LatestPostsFeed, AtomLatestPostsFeed
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required

POST_PUB_DATE_FIELD = "pub_date"
POST_CONTEXT_OBJECT_NAME = "post"
PAGE_TITLE_FIELD = "page_title"
META_DESCRIPTION_FIELD = "meta_description"
ROOT_CATEGORY_FIELD = "root_category"


class BlogArchiveBaseView():
    """
    Collects settings that are common to all GenericArchiveViews
    """
    date_field = POST_PUB_DATE_FIELD
    queryset = Post.published.all()
    allow_empty = True
    make_object_list = True
    month_format = '%m'


class BlogArchiveView(BlogArchiveBaseView, ArchiveIndexView):

    def get_context_data(self, **kwargs):
        """
        Adds a breakdown_by_year variable to the context.

        The variable is a dictionary mapping from year to the number of posts
        that were published within that year.
        """
        data = super(BlogArchiveView, self).get_context_data(**kwargs)
        breakdown_by_year = collections.defaultdict(list)

        for post in data['latest']:
            breakdown_by_year[post.pub_date.year].append(post)
        # django templates can't loop over defaultdicts, change back to a dict
        data['breakdown_by_year'] = dict(breakdown_by_year)
        data[PAGE_TITLE_FIELD] = 'Archive'
        data[ROOT_CATEGORY_FIELD] = 'archive'
        return data


class BlogYearArchiveView(BlogArchiveBaseView, YearArchiveView):

    def get_context_data(self, **kwargs):
        data = super(BlogYearArchiveView, self).get_context_data(**kwargs)
        data[PAGE_TITLE_FIELD] = "%(year)s Archive" % self.kwargs
        return data


class BlogMonthArchiveView(BlogArchiveBaseView, MonthArchiveView):

    def get_context_data(self, **kwargs):
        data = super(BlogMonthArchiveView, self).get_context_data(**kwargs)
        month = datetime.date(int(self.kwargs['year']), int(self.kwargs['month']), 1)
        data[PAGE_TITLE_FIELD] = "%s Archive" % month.strftime("%B %Y")
        return data


class BlogDayArchiveView(BlogArchiveBaseView, DayArchiveView):

    def get_context_data(self, **kwargs):
        data = super(BlogDayArchiveView, self).get_context_data(**kwargs)
        day = datetime.date(int(self.kwargs['year']), int(self.kwargs['month']), int(self.kwargs['day']))
        data[PAGE_TITLE_FIELD] = "%s Archive" % day.strftime("%B %d, %Y")
        return data


class BlogPostDetailView(BlogArchiveBaseView, DateDetailView):
    allow_empty = False
    slug_field = 'title_slug'
    context_object_name = POST_CONTEXT_OBJECT_NAME

    def get_context_data(self, **kwargs):
        data = super(BlogPostDetailView, self).get_context_data(**kwargs)
        data[PAGE_TITLE_FIELD] = data[POST_CONTEXT_OBJECT_NAME].title
        data[META_DESCRIPTION_FIELD] = data[POST_CONTEXT_OBJECT_NAME].synopsis
        data[ROOT_CATEGORY_FIELD] = 'archive'
        return data


class BlogDraftPostDetailView(BlogPostDetailView):
    queryset = Post.objects.filter(is_draft=True)

    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(BlogDraftPostDetailView, self).dispatch(request, *args, **kwargs)


def index(request):
    try:
        latest = Post.published.select_related().latest(POST_PUB_DATE_FIELD)
    except ObjectDoesNotExist:
        latest = None
    return render_to_response("blog/post_detail.html",
                              {POST_CONTEXT_OBJECT_NAME: latest,
                               PAGE_TITLE_FIELD: "Blog",
                               ROOT_CATEGORY_FIELD: "most-recent",
                               META_DESCRIPTION_FIELD: latest and latest.synopsis},
                              context_instance=RequestContext(request))


class FeedsView(TemplateView):
    template_name = "blog/feeds.html"

    def get_context_data(self, **kwargs):
        data = super(FeedsView, self).get_context_data(**kwargs)
        data.update({
            'title': 'Latest Blog Postings',
            'rss_version': LatestPostsFeed.feed_version,
            'atom_version': AtomLatestPostsFeed.feed_version
        })
        return data