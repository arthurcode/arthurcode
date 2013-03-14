__author__ = 'rhyanarthur'

from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from blog.models import Post
import datetime
from django.utils.feedgenerator import Atom1Feed, Rss201rev2Feed


class LatestPostsFeed(Feed):
    NUM_POSTS = 4

    title = "Arthurcode.com Latest Blog Postings"
    author_name = "Rhyan Arthur"
    author_email = "rhyan.arthur@gmail.com"
    feed_copyright = "Copyright (c) 2013, arthurcode.com"
    categories = ("web development", "django")
    feed_type = Rss201rev2Feed  # RSS 2.01
    feed_version = "RSS 2.01"
    description = "The latest in django web-development from Rhyan Arthur, founder of arthurcode.com."

    def link(self):
        return reverse('index')

    def items(self):
        return Post.objects.order_by('-pub_date')[:LatestPostsFeed.NUM_POSTS]

    def item_title(self, post):
        return post.title

    def item_description(self, post):
        return post.synopsis

    def item_link(self, post):
        return post.get_absolute_url()

    def item_guid_is_permalink(self):
        return True

    def item_author_name(self, post):
        return post.get_author_name()

    def item_author_email(self, post):
        return post.get_author_email()

    def item_author_link(self, post):
        # assumes that a single author posts on this blog
        return self.author_link()

    def item_pubdate(self, post):
        """
        This method requires a datetime.datetime return value, so we need to convert out datetime.date pub_date.
        """
        return datetime.datetime.combine(post.pub_date, datetime.time(0, 0, 0, 0))

    def item_categories(self, post):
        # TODO: return tags when I add them
        return LatestPostsFeed.categories

    def item_copyright(self, post):
        return LatestPostsFeed.feed_copyright

    def feed_url(self):
        return reverse('rss')

    def author_link(self):
        return self.link()


class AtomLatestPostsFeed(LatestPostsFeed):
    feed_type = Atom1Feed
    subtitle = LatestPostsFeed.description
    feed_version = "Atom 1.0"