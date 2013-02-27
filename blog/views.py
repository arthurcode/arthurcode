from blog.models import Post
from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView, ArchiveIndexView


class BlogArchiveView(ArchiveIndexView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    allow_empty = True


class BlogYearArchiveView(YearArchiveView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    make_object_list = True
    allow_empty = True


class BlogMonthArchiveView(MonthArchiveView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    make_object_list = True
    allow_empty = True


class BlogDayArchiveView(DayArchiveView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    make_object_list = True
    allow_empty = True

