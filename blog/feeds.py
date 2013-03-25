__author__ = 'rhyanarthur'

from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from blog.models import Post
import datetime
from django.utils.feedgenerator import Atom1Feed, Rss201rev2Feed, rfc3339_date


# BEGIN PATCH - https://code.djangoproject.com/ticket/14656
# 'published' element missing from atom feeds
Atom1Feed._add_item_elements = Atom1Feed.add_item_elements


def atom1feed_add_item_elements_patched(self, handler, item, *args, **kwargs):
    if item['pubdate'] is not None:
        handler.addQuickElement(u"published", rfc3339_date(item['pubdate']).decode('utf-8'))
        # include args, kwargs for future compatibility
    self._add_item_elements(handler, item, *args, **kwargs)

Atom1Feed.add_item_elements = atom1feed_add_item_elements_patched
# - END PATCH


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
        return Post.published.order_by('-pub_date')[:LatestPostsFeed.NUM_POSTS]

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

    def item_pubdate(self, post):
        """
        This method requires a datetime.datetime return value, so we need to convert out datetime.date pub_date.
        TODO: look into using the last-modified date for Atom feeds
        """
        return datetime.datetime.combine(post.pub_date, datetime.time(0, 0, 0, 0))

    def item_categories(self, post):
        # TODO: return tags when I add them
        return LatestPostsFeed.categories

    def item_copyright(self, post):
        return LatestPostsFeed.feed_copyright

    def feed_url(self):
        return reverse('rss')


class AtomLatestPostsFeed(LatestPostsFeed):
    feed_type = Atom1Feed
    subtitle = LatestPostsFeed.description
    feed_version = "Atom 1.0"

    def feed_url(self):
        return reverse('atom')