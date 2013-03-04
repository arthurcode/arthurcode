from blog.models import Post
from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView, ArchiveIndexView, DateDetailView
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response
from django.template import RequestContext
import collections

POST_PUB_DATE_FIELD = "pub_date"
POST_CONTEXT_OBJECT_NAME = "post"

class BlogArchiveBaseView():
    """
    Collects settings that are common to all GenericArchiveViews
    """
    date_field = POST_PUB_DATE_FIELD
    queryset = Post.objects.all()
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
        data = super(ArchiveIndexView, self).get_context_data(**kwargs)
        breakdown_by_year = collections.defaultdict(list)

        for post in data['latest']:
            breakdown_by_year[post.pub_date.year].append(post)
        # django templates can't loop over defaultdicts, change back to a dict
        data['breakdown_by_year'] = dict(breakdown_by_year)
        return data



class BlogYearArchiveView(BlogArchiveBaseView, YearArchiveView):
    pass


class BlogMonthArchiveView(BlogArchiveBaseView, MonthArchiveView):
    pass


class BlogDayArchiveView(BlogArchiveBaseView, DayArchiveView):
    pass


class BlogPostDetailView(BlogArchiveBaseView, DateDetailView):
    allow_empty = False
    slug_field = 'title_slug'
    context_object_name = POST_CONTEXT_OBJECT_NAME


def index(request):
    try:
        latest = Post.objects.latest(POST_PUB_DATE_FIELD)
    except ObjectDoesNotExist:
        latest = None
    return render_to_response("blog/post_detail.html",
                              {POST_CONTEXT_OBJECT_NAME: latest},
                              context_instance=RequestContext(request))

