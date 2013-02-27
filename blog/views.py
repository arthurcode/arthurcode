from blog.models import Post
from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView, ArchiveIndexView, DateDetailView


class BlogArchiveBaseView():
    """
    Collects settings that are common to all GenericArchiveViews
    """
    date_field = "pub_date"
    queryset = Post.objects.all()
    allow_empty = True
    make_object_list = True
    month_format = '%m'


class BlogArchiveView(BlogArchiveBaseView, ArchiveIndexView):
    pass


class BlogYearArchiveView(BlogArchiveBaseView, YearArchiveView):
    pass


class BlogMonthArchiveView(BlogArchiveBaseView, MonthArchiveView):
    pass


class BlogDayArchiveView(BlogArchiveBaseView, DayArchiveView):
    pass

class BlogPostDetailView(BlogArchiveBaseView, DateDetailView):
    allow_empty = False
    slug_field = 'title_slug'
    context_object_name = 'post'

