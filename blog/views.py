from blog.models import Post
from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView

class BlogYearArchiveView(YearArchiveView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    make_object_list = True


class BlogMonthArchiveView(MonthArchiveView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    make_object_list = True


class BlogDayArchiveView(DayArchiveView):
    queryset = Post.objects.all()
    date_field = "pub_date"
    make_object_list = True

