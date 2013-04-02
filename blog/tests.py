from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import AuthorProfile, Post
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core.urlresolvers import reverse
from blog import validators
from django.test.client import Client
from django.test.utils import override_settings
import datetime, time
from monthdelta import MonthDelta
from comments.forms import MPTTCommentForm
from comments.models import MPTTComment
from comments.forms import CommentSecurityForm
from bs4 import BeautifulSoup
from feeds import LatestPostsFeed
import comments as comments_app
from mock import patch


# -----------------------------
# MODEL TESTS
#------------------------------


class AuthorProfileTest(TestCase):

    def setUp(self):
        self.user = User(username="foo", password="whatever")
        self.user.full_clean()
        self.user.save()
        self.blanks = ["", "  ", u"", u"  "]

    def test_create_fails_no_user_email(self):

        for email in self.blanks:
            self.user.email = email
            # don't clean the model since it will complain that the e-mail address is blank
            self.user.save()

            with self.assertRaises(ValidationError) as cm:
                self.create_profile(user=self.user, pen_name="doesn't matter")
            self.assertIn(AuthorProfile.ERROR_CREATE_NO_EMAIL, str(cm.exception))

    def test_create_default_pen_name(self):
        self.user.email = "me@example.com"
        self.user.first_name = "Rhyan"
        self.user.last_name = "Arthur"
        self.user.full_clean()
        self.user.save()

        expected_default_pen_name = "%s %s" % (self.user.first_name, self.user.last_name)

        for pen_name in self.blanks:
            author = self.create_profile(user=self.user, pen_name=pen_name)
            self.assertEqual(expected_default_pen_name, author.pen_name)
            author.delete()

    def test_create_fails_no_default_pen_name(self):
        invalid_names = ("Rhyan", ""), ("", "Arthur"), ("", "")

        for (first_name, last_name) in invalid_names:
            self.user.first_name = first_name
            self.user.last_name = last_name
            self.user.email = "me@example.com"
            self.user.full_clean()
            self.user.save()

            for pen_name in self.blanks:
                with self.assertRaises(ValidationError) as cm:
                    self.create_profile(user=self.user, pen_name=pen_name)
                self.assertIn(AuthorProfile.ERROR_CREATE_NO_FIRST_LAST_NAME, str(cm.exception))

    def test_create_unique_pen_name(self):
        self.user.email = "me@example.com"
        self.user.full_clean()
        self.user.save()

        self.create_profile(user=self.user, pen_name="Rhyan Arthur")
        with self.assertRaises(ValidationError) as cm:
            self.create_profile(user=self.user, pen_name="Rhyan Arthur")

        self.create_profile(user=self.user, pen_name="Rhyan Laine Arthur")

    def create_profile(self, *args, **kwargs):
        author = AuthorProfile(*args, **kwargs)
        author.full_clean()
        author.save()
        return author


class PostTest(TestCase):

    def setUp(self):
        self.user = User(username="arthur", password="whocares", email="me@example.com")
        self.user.full_clean()
        self.user.save()

        self.author = AuthorProfile(user=self.user, pen_name="Captain Yoga Pants")
        self.author.full_clean()
        self.author.save()

        self.blanks = ["", "  ", u"", u"  "]

    def test_create_post(self):
        post = create_post(title="Why I Wear Yoga Pants", title_slug="slug", author=self.author, body="hi",
                                synopsis="some synopsis", tags=["tag1", "tag2"])
        self.assertIsNotNone(post.pub_date)
        self.assertIsNotNone(post.mod_date)
        self.assertEqual(post.pub_date, post.mod_date)
        self.assertEqual(self.author.pen_name, post.get_author_name())
        self.assertEqual(self.user.email, post.get_author_email())
        self.assertEqual(post.is_draft, False)
        tags = post.tags.all()
        self.assertEqual(2, len(tags))
        self.assertEqual("tag1", tags[0].name)
        self.assertEqual("tag2", tags[1].name)

    def test_create_post_title_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                create_post(title=blank, author=self.author)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_slug_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                create_post(title_slug=blank, author=self.author)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_body_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                create_post(author=self.author, body=blank)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_synopsis_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                create_post(author=self.author, synopsis=blank)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_duplicate_titles_allowed(self):
        title = "Hello, I am a title."
        # as long as the slugs are different this should be allowed
        create_post(title=title, title_slug="slug1", author=self.author)
        create_post(title=title, title_slug="slug2", author=self.author)

    def test_duplicate_slugs_not_allowed(self):
        slug = "slug"
        create_post(title="title", title_slug=slug, author=self.author)
        with self.assertRaises(ValidationError) as cm:
            create_post(title="new title", title_slug=slug, author=self.author)
        self.assertIn("title_slug", str(cm.exception))

    def test_get_absolute_url(self):
        post = create_post(author=self.author)
        url = post.get_absolute_url()

        # check that the url is sane
        c = Client()
        response = c.get(url)
        self.assertEqual(200, response.status_code)

    def test_comments_enabled(self):
        post = create_post(author=self.author)
        self.assertTrue(post.enable_comments)
        self.assertTrue(post.is_commenting_enabled())

        post.enable_comments = False
        post.full_clean()
        post.save()
        self.assertFalse(post.enable_comments)
        self.assertFalse(post.is_commenting_enabled())

        post.enable_comments = None
        with self.assertRaises(IntegrityError) as cm:
            post.full_clean()
            post.save()
        self.assertIn("enable_comments", str(cm.exception))

    def test_draft_post(self):
        today = datetime.date.today()
        two_days_ago = today - datetime.timedelta(2)
        post = create_post(author=self.author, is_draft=True, pub_date=two_days_ago)
        self.assertTrue(post.is_draft)
        self.assertEqual(0, Post.published.count())
        self.assertEqual(two_days_ago, post.pub_date)

        post.publish()
        self.assertFalse(post.is_draft)
        self.assertEqual(today, post.pub_date)
        self.assertEqual(today, post.mod_date)
        self.assertEqual(1, Post.published.count())


#-----------------------------
# VIEW TESTS
#-----------------------------

class ViewTests(TestCase):

    def setUp(self):
        self.c = Client()
        self.user = User.objects.create_user('arthur', 'me@example.com', 'whocares')
        self.user.is_staff = True
        self.user.full_clean()
        self.user.save()
        self.author = AuthorProfile(user=self.user, pen_name="Captain Yoga Pants")
        self.author.full_clean()
        self.author.save()

    def test_archive_templates_used(self):
        today = datetime.date.today()
        create_post(pub_date=today, author=self.author)

        response = self.c.get(self.get_archive_url(today))
        self.assertTemplateUsed(response, "blog/post_archive.html")

        response = self.c.get(self.get_archive_url(today, 'year'))
        self.assertTemplateUsed(response, "blog/post_archive_year.html")

        response = self.c.get(self.get_archive_url(today, 'month'))
        self.assertTemplateUsed(response, "blog/post_archive_month.html")

        response = self.c.get(self.get_archive_url(today, 'day'))
        self.assertTemplateUsed(response, "blog/post_archive_day.html")

    def test_empty_views_allowed(self):
        # create a draft post - these should never show up in the archives
        post = create_post(author=self.author, is_draft=True)

        # we don't want archive views with no posts to throw 404
        posts = Post.published.all()
        self.assertEqual(0, len(posts))
        today = datetime.date.today()

        response = self.c.get(self.get_archive_url(today))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "No posts in the archive", 1)
        self.verify_generic_archive_properties(response, date=today)

        response = self.c.get(self.get_archive_url(today, 'year'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "No posts for year %s" % today.year, 1)
        self.verify_generic_archive_properties(response, date=today, level='year')

        response = self.c.get(self.get_archive_url(today, 'month'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "No posts for", 1)
        self.verify_generic_archive_properties(response, date=today, level='month')

        response = self.c.get(self.get_archive_url(today, 'day'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "No posts for", 1)
        self.verify_generic_archive_properties(response, date=today, level='day')

    def test_archive_non_empty_views(self):
        post_date = datetime.date(2012, 8, 22)
        off_by_one_day = datetime.date(2012, 8, 23)
        off_by_one_month = datetime.date(2012, 7, 22)
        off_by_one_year = datetime.date(2011, 8, 22)

        post = create_post(pub_date=post_date, author=self.author)

        self.assert_post_in_archive(post_date, post, level='day')
        self.assert_post_in_archive(post_date, post, level='month')
        self.assert_post_in_archive(post_date, post, level='year')
        self.assert_post_in_archive(post_date, post, level='all')

        self.assert_post_not_in_archive(off_by_one_day, post, level='day')
        self.assert_post_not_in_archive(off_by_one_month, post, level='day')
        self.assert_post_not_in_archive(off_by_one_month, post, level='month')
        self.assert_post_not_in_archive(off_by_one_year, post, level='day')
        self.assert_post_not_in_archive(off_by_one_year, post, level='month')
        self.assert_post_not_in_archive(off_by_one_year, post, level='year')

    def test_archive_multiple_posts(self):
        post_date_1 = datetime.date(2011, 8, 23)
        post_date_2 = datetime.date(2013, 1, 1)

        post_1 = create_post(pub_date=post_date_1, author=self.author)
        post_2 = create_post(pub_date=post_date_2, author=self.author)
        self.assert_post_in_archive(post_date_1, post_1, level='all')
        self.assert_post_in_archive(post_date_2, post_2, level='all')

    def test_post_detail_view(self):
        post_date = datetime.date.today()
        post = create_post(pub_date=post_date, author=self.author)
        response = self.c.get(post.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, post.title)
        self.assertContains(response, post.get_author_name())
        self.assert_contains_link(response, self.get_archive_url())
        self.assert_does_not_contain_link(response, post.get_absolute_url())
        self.assertNotContains(response, "last-modified")
        self.assert_page_title_is(response, post.title)
        self.assert_meta_desc_is(response, post.synopsis)
        self.assert_has_single_comment_form(response)

        post_date = datetime.date.today() - datetime.timedelta(1)
        post = create_post(pub_date=post_date, author=self.author)
        response = self.c.get(post.get_absolute_url())
        # last modified will default to today's date, which is one day later than the publication date
        self.assertContains(response, "last-modified")
        self.assert_has_single_comment_form(response)

        bogus_url = post.get_absolute_url().rstrip("/") + "garbage/"
        response = self.c.get(bogus_url)
        self.assertEqual(404, response.status_code)

    def test_draft_post_detail_view(self):
        draft_post = create_post(author=self.author, is_draft=True)
        params = {'year': draft_post.pub_date.year,
                  'month': draft_post.pub_date.month,
                  'day': draft_post.pub_date.day,
                  'slug': draft_post.title_slug}

        # verify that the draft post cannot be viewed at its 'public' url
        public_url = reverse('post_detail', kwargs=params)
        response = self.c.get(public_url)
        self.assertEqual(404, response.status_code)

        # assert that the private url can only be viewed by a staff member
        private_url = draft_post.get_absolute_url()
        self.assertNotEqual(public_url, private_url)
        response = self.c.get(private_url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "admin/login.html")

        # login as a staff member
        login_successful = self.c.login(username=self.user.username, password='whocares')
        self.assertTrue(login_successful)

        response = self.c.get(private_url)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")

        # after the draft has been published it should be visible at the public url
        draft_post.publish()
        response = self.c.get(public_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(public_url, draft_post.get_absolute_url())
        self.assertTemplateUsed(response, "blog/post_detail.html")

        # assert that the draft is no longer visible at the private url
        response = self.c.get(private_url)
        self.assertEqual(404, response.status_code)

    def test_index(self):
        # test that we don't die a horrible death when the index is rendered when there are no posts in the database
        response = self.c.get(reverse('index'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, "No post")

        post_1 = create_post(pub_date=datetime.date(2013, 01, 02), author=self.author)
        post_2 = create_post(pub_date=datetime.date(2013, 01, 03), author=self.author)
        # the latest post is a draft - it shouldn't show up on the home page
        draft_post = create_post(pub_date=datetime.date(2013, 01, 04), author=self.author, is_draft=True)
        response = self.c.get(reverse('index'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assert_contains_link(response, reverse('index'))
        self.assert_page_title_is(response, "Blog")

        # assert that only the latest (non-draft) post is rendered on the main page
        # and that there is a permalink to the post's url
        self.assertContains(response, post_2.title)
        self.assertNotContains(response, post_1.title)
        self.assert_contains_link(response, post_2.get_absolute_url())
        self.assert_does_not_contain_link(response, post_1.get_absolute_url())
        self.assert_contains_link(response, reverse('index'))
        self.assert_meta_desc_is(response, post_2.synopsis)
        self.assert_has_single_comment_form(response)

        # publish the draft post and assert that now it appears on the home page
        draft_post.publish()
        response = self.c.get(reverse('index'))
        self.assertEqual(200, response.status_code)
        self.assertContains(response, draft_post.title)
        self.assertNotContains(response, post_2.title)

    def test_about_and_contact_views(self):
        about_url = reverse('about')
        contact_url = reverse('contact')
        index_url = reverse('index')

        # about view
        response = self.c.get(about_url)
        self.assertEqual(200, response.status_code)
        self.assert_page_title_is(response, "About")
        self.assert_contains_link(response, index_url)
        self.assert_contains_link(response, contact_url)

        # contact view
        response = self.c.get(contact_url)
        self.assertEqual(200, response.status_code)
        self.assert_page_title_is(response, "Contact")
        self.assert_contains_link(response, about_url)
        self.assert_contains_link(response, index_url)

    def test_rss_view(self):
        # make more posts than will be displayed in the feeds
        posts = make_consecutive_daily_posts(LatestPostsFeed.NUM_POSTS + 3, author=self.author, tags=["tag1", "tag2"])
        # create a draft post - this shouldn't be shown in the feeds
        create_post(author=self.author, is_draft=True)

        rss_url = reverse('rss')
        response = self.c.get(rss_url)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        rss = soup.find('rss')
        self.assertIsNotNone(rss)

        title = rss.find('title').text
        self.assertEquals(LatestPostsFeed.title, title)
        link = rss.find('link').text
        self.assertTrue(link.endswith(reverse('index')))
        description = rss.find('description').text
        self.assertEquals(LatestPostsFeed.description, description)
        copy_right = rss.find('copyright').text
        self.assertEquals(LatestPostsFeed.feed_copyright, copy_right)

        items = rss.find_all('item')
        self.assertEquals(LatestPostsFeed.NUM_POSTS, len(items))

        for item, post in zip(items, posts):
            title = item.find('title').text
            self.assertEquals(post.title, title)
            link = item.find('link').text
            self.assertTrue(link.endswith(post.get_absolute_url()))
            description = item.find('description').text
            self.assertEquals(post.synopsis, description)
            author = item.find('author').text
            self.assertEquals("%s (%s)" % (post.get_author_email(), post.get_author_name()), author)
            guid = item.find('guid').text
            self.assertEquals(link, guid)
            categories = item.find_all('category')
            self.assertEquals(2, len(categories))
            self.assertEquals("tag1", categories[0].text)
            self.assertEquals("tag2", categories[1].text)


    def test_atom_view(self):
        # make more posts than will be displayed in the feeds
        posts = make_consecutive_daily_posts(LatestPostsFeed.NUM_POSTS + 3, author=self.author, tags=["tag3", "tag4"])
        # create a draft post - this shouldn't be shown in the feeds
        create_post(author=self.author, is_draft=True)

        atom_url = reverse('atom')
        response = self.c.get(atom_url)
        self.assertEquals(200, response.status_code)
        soup = BeautifulSoup(response.content)
        feed = soup.find('feed')
        self.assertIsNotNone(feed)

        title = feed.find('title').text
        self.assertEquals(LatestPostsFeed.title, title)
        link = feed.find('link', {'rel': 'alternate'})
        link_href = link.attrs['href']
        self.assertTrue(link_href.endswith(reverse('index')))
        self.assertEquals(link_href, feed.find('id').text)
        link = feed.find('link', {'rel': 'self'})
        self.assertTrue(link.attrs['href'].endswith(atom_url))

        author = feed.find('author')
        self.assertEquals(LatestPostsFeed.author_name, author.find('name').text)
        self.assertEquals(LatestPostsFeed.author_email, author.find('email').text)
        subtitle = feed.find('subtitle')
        self.assertEquals(LatestPostsFeed.description, subtitle.text)
        rights = feed.find('rights')
        self.assertEquals(LatestPostsFeed.feed_copyright, rights.text)
        entries = feed.find_all('entry')
        self.assertEquals(LatestPostsFeed.NUM_POSTS, len(entries))

        for entry, post in zip(entries, posts):
            title = entry.find('title').text
            self.assertEquals(post.title, title)
            link = entry.find('link')
            link_href = link.attrs['href']
            self.assertTrue(link_href.endswith(post.get_absolute_url()))

            author = entry.find('author')
            self.assertEquals(post.get_author_name(), author.find('name').text)
            self.assertEquals(post.get_author_email(), author.find('email').text)
            self.assertEquals(link_href, entry.find('id').text)
            summary = entry.find('summary')
            self.assertEquals(post.synopsis, summary.text)
            # assert the atom feed item has a 'published' element (django bug 14656)
            self.assertIsNotNone(entry.find('published'))

            categories = entry.find_all('category')
            self.assertEquals(2, len(categories))
            self.assertEquals("tag3", categories[0].attrs['term'])
            self.assertEquals("tag4", categories[1].attrs['term'])

    def test_related_content(self):
        tags = ["django", "web development", "css"]
        posts = make_consecutive_daily_posts(10, author=self.author, tags=tags)
        # since they all have the same tags, each should have 9 similar posts
        post = posts[0]
        response = self.c.get(post.get_absolute_url())
        soup = BeautifulSoup(response.content)
        related = soup.find('div', 'related-content')
        self.assertIsNotNone(related, "The related-content div is missing")
        related_posts = related.find_all('a')
        self.assertEquals(5, len(related_posts))

        titles = [post.title for post in posts[1:]]
        for related_post in related_posts:
            self.assertIn(related_post.text, titles)

    def assert_post_in_archive(self, date, post, level='all'):
        url = self.get_archive_url(date, level)
        response = self.c.get(url)
        self.assertContains(response, post.title)
        self.verify_generic_archive_properties(response, date=date, level=level)

        # verify that there is a breakdown by year
        if level == 'all':
            self.assertContains(response, '<li>%s</li>' % date.year, 1, html=True)

    def assert_post_not_in_archive(self, date, post, level='all'):
        url = self.get_archive_url(date, level)
        response = self.c.get(url)
        self.assertNotContains(response, post.title)
        self.verify_generic_archive_properties(response, date=date, level=level)

    def assert_contains_link(self, response, url, count=None):
        fragment = "href=\"%s\"" % url
        self.assertContains(response, fragment, count=count)

    def assert_does_not_contain_link(self, response, url):
        self.assert_contains_link(response, url, count=0)

    def assert_page_title_is(self, response, title):
        self.assertContains(response, "<title>%s | Arthurcode</title>" % title, html=True)

    def assert_meta_desc_is(self, response, desc):
        meta = '<meta name="description" content="%s"/>' % desc
        self.assertContains(response, meta, html=True)

    def assert_has_single_comment_form(self, response):
        soup = BeautifulSoup(response.content)
        forms = soup.find_all('form', 'comment')
        self.assertEquals(1, len(forms))
        labels = forms[0].find_all('label')

        # honeypot, name, email and comment
        self.assertEquals(4, len(labels))

        # honeypot is optional
        label_honeypot = forms[0].find('label', {'for': 'id_honeypot'})
        self.assertIsNotNone(label_honeypot.find('span', 'optional-text'))
        self.assertIsNone(label_honeypot.find('span', 'required-text'))

        # name is required
        label_name = forms[0].find('label', {'for': 'id_name'})
        self.assertIsNotNone(label_name.find('span', 'required-text'))
        self.assertIsNone(label_name.find('span', 'optional-text'))

        # email is required
        label_email = forms[0].find('label', {'for': 'id_email'})
        self.assertIsNotNone(label_email.find('span', 'required-text'))
        self.assertIsNone(label_email.find('span', 'optional-text'))

        # comment is required
        label_comment = forms[0].find('label', {'for': 'id_comment'})
        self.assertIsNotNone(label_comment.find('span', 'required-text'))
        self.assertIsNone(label_comment.find('span', 'optional-text'))

    def verify_generic_archive_properties(self, response, date=None, level='all'):
        # all pages should have a link to the archives in the footer
        self.assert_contains_link(response, self.get_archive_url())
        # all pages should have a link to the main blog page
        self.assert_contains_link(response, reverse('index'))

        today = datetime.date.today()

        if level == 'all':
            self.assert_page_title_is(response, 'Archive')

        elif level == 'year':
            self.assert_page_title_is(response, "%s Archive" % date.year)

        elif level == 'month':
            self.assert_page_title_is(response, "%s Archive" % date.strftime("%B %Y"))
            previous_month = date + MonthDelta(-1)
            self.assert_contains_link(response, self.get_archive_url(date=previous_month, level='month'))
            next_month = date + MonthDelta(+1)
            next_month.replace(next_month.year, next_month.month, 1)
            # make sure it isn't a future month
            if next_month <= today:
                self.assert_contains_link(response, self.get_archive_url(date=next_month, level='month'))

        elif level == 'day':
            self.assert_page_title_is(response, "%s Archive" % date.strftime("%B %d, %Y"))
            previous_day = date - datetime.timedelta(1)
            self.assert_contains_link(response, self.get_archive_url(date=previous_day, level='day'))
            next_day = date + datetime.timedelta(1)
            # make sure it isn't a future day
            if next_day <= today:
                self.assert_contains_link(response, self.get_archive_url(date=next_day, level='day'))

    def get_archive_url(self, date=None, level='all'):
        """
        level must be one of [all, year, month, day]
        """
        if level == 'all':
            return reverse("archive")
        if level == 'year':
            params = {'year': date.year}
            return reverse("year_archive", kwargs=params)
        if level == 'month':
            params = {'year': date.year, 'month': date.month}
            return reverse("month_archive", kwargs=params)
        if level == 'day':
            params = {'year': date.year, 'month': date.month, 'day': date.day}
            return reverse("day_archive", kwargs=params)
        raise Exception("Unrecognized level: %s" % level)


class AkismetPostMock():

    VERIFY_KEY_PATH = "/1.1/verify-key"
    COMMENT_CHECK_PATH = "/1.1/comment-check"
    SUBMIT_SPAM_PATH = "/1.1/submit-spam"
    SUBMIT_HAM_PATH = "/1.1/submit-ham"

    DEFAULTS = {
        VERIFY_KEY_PATH: ("valid", 200),     # valid key
        COMMENT_CHECK_PATH: ("false", 200),  # not spam
        SUBMIT_SPAM_PATH: ("", 200),         # success
        SUBMIT_HAM_PATH: ("", 200)           # success
    }

    def __init__(self):
        self.vals = AkismetPostMock.DEFAULTS
        self.post_args = []

    def post(self, *args):
        self.post_args.append(args)
        return self.vals[args[2]]

    def set_comment_is_spam(self, spam):
        self.vals[AKISMET_POST_MOCK.COMMENT_CHECK_PATH] = (str(spam).lower(), 200)

    def set_check_comment_response(self, response, status):
        self.vals[AKISMET_POST_MOCK.COMMENT_CHECK_PATH] = (response, status)

    def set_valid_key(self, valid):
        if valid:
            value = "valid"
        else:
            value = "invalid"
        self.vals[AKISMET_POST_MOCK.VERIFY_KEY_PATH] = (value, 200)

    def set_check_key_response(self, response, status):
        self.vals[AKISMET_POST_MOCK.VERIFY_KEY_PATH] = (response, status)

    def set_submit_ham_response(self, status):
        self.vals[AKISMET_POST_MOCK.SUBMIT_HAM_PATH] = ("", status)

    def set_submit_spam_response(self, status):
        self.vals[AKISMET_POST_MOCK.SUBMIT_SPAM_PATH] = ("", status)

    def restore_defaults(self):
        self.vals = AkismetPostMock.DEFAULTS
        self.post_args = []

AKISMET_POST_MOCK = AkismetPostMock()


@override_settings(AKISMET_KEY="myfakekey")
@patch('comments.akismet.__post', AKISMET_POST_MOCK.post)
class CommentingTest(TestCase):

    USER_AGENT = 'Mozilla/5.0'

    def setUp(self):
        self.c = Client(HTTP_USER_AGENT=CommentingTest.USER_AGENT)
        self.user = User.objects.create_superuser("username", "someone@fake.com", "password")
        self.author = AuthorProfile(user=self.user, pen_name="Captain Yoga Pants")
        self.author.full_clean()
        self.author.save()
        AKISMET_POST_MOCK.restore_defaults()

    def test_use_mptt_comments(self):
        """
        Test that we have properly customized the built-in comments app.
        """
        self.assertEqual(MPTTComment, comments_app.get_model())
        self.assertEqual(MPTTCommentForm, comments_app.get_form())

    def test_post_comments(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post, parent=None)
        url = comments_app.get_form_target()
        response = self.c.post(url, data, follow=True)
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "comments/posted.html")

        # test that 1 comment has been created
        self.assertEqual(1, MPTTComment.objects.all().count())
        comment = MPTTComment.objects.all()[0]
        self.assertIsNone(comment.parent_id)
        self.assertEqual(str(post.id), comment.object_pk)

        # reply to the previous comment
        data = self.make_post_comment_data(post, parent=comment)
        response = self.c.post(url, data, follow=True)
        self.assertEquals(200, response.status_code)
        self.assertTemplateUsed(response, "comments/posted.html")
        self.assertEqual(2, MPTTComment.objects.all().count())

        # the original comment should now have one child
        self.assertEqual(1, comment.children.all().count())
        reply = comment.children.all()[0]
        self.assertEqual(comment.id, reply.parent_id)

    def test_disable_comments(self):
        post = create_post(enable_comments=False, author=self.author)
        data = self.make_post_comment_data(post, parent=None)
        url = comments_app.get_form_target()
        response = self.c.post(url, data, follow=True)
        self.assertEqual(400, response.status_code)
        self.assertEqual(0, MPTTComment.objects.all().count())

        post.enable_comments = True
        post.save()
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MPTTComment.objects.all().count())

    def test_comment_form_email_error(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post, email="garbage-email-address")
        self.assert_comment_form_error(data, 'email', 'Enter a valid e-mail address.')

        data = self.make_post_comment_data(post, email="")
        self.assert_comment_form_error(data, 'email', 'This field is required.')

    def test_comment_form_name_error(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post, name="")
        self.assert_comment_form_error(data, 'name', 'This field is required.')

    def test_comment_form_comment_error(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post, comment="")
        self.assert_comment_form_error(data, 'comment', 'This field is required.')

    def test_comments_from_authenticated_users(self):
        self.assertEqual(0, MPTTComment.objects.all().count())
        url = comments_app.get_form_target()
        post = create_post(author=self.author)

        login_successful = self.c.login(username=self.user.username, password="password")
        self.assertTrue(login_successful, "Login attempt unexpectedly failed.")

        # even if name and e-mail are left blank, we should use the values from the user's profile
        data = self.make_post_comment_data(post, name="", email="")
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        comments = MPTTComment.objects.all()
        self.assertEqual(1, len(comments))
        comment = comments[0]

        self.assertEqual(self.user.username, comment.user.username)
        self.assertEqual(self.user.email, comment.user.email)

    def test_comment_marked_spam(self):
        comment = self._make_spam_comment()
        self.assertTrue(comment.is_spam)

    def test_comments_allowed_invalid_key(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post)
        url = comments_app.get_form_target()
        AKISMET_POST_MOCK.set_valid_key(False)
        AKISMET_POST_MOCK.set_comment_is_spam(True)

        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        comments = MPTTComment.objects.all()
        self.assertEqual(1, len(comments))
        comment = comments[0]

        self.assertFalse(comment.is_spam)
        self.assertTrue(comment.is_public)

    def test_comments_allowed_akismet_key_error(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post)
        url = comments_app.get_form_target()
        AKISMET_POST_MOCK.set_check_key_response('', 404)
        AKISMET_POST_MOCK.set_comment_is_spam(True)

        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        comments = MPTTComment.objects.all()
        self.assertEqual(1, len(comments))
        comment = comments[0]

        self.assertFalse(comment.is_spam)
        self.assertTrue(comment.is_public)

    def test_comments_allowed_akismet_check_spam_error(self):
        post = create_post(author=self.author)
        data = self.make_post_comment_data(post)
        url = comments_app.get_form_target()
        AKISMET_POST_MOCK.set_valid_key(True)
        AKISMET_POST_MOCK.set_check_comment_response('', 404)

        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        comments = MPTTComment.objects.all()
        self.assertEqual(1, len(comments))
        comment = comments[0]

        self.assertFalse(comment.is_spam)
        self.assertTrue(comment.is_public)

    def test_approve_comments_clears_spam_and_notifies_akismet(self):
        # make sure the logged in user has permissions to moderate comments (it's a superuser)
        login_successful = self.c.login(username=self.user.username, password="password")
        self.assertTrue(login_successful)

        comment = self._make_spam_comment()
        self.assertTrue(comment.is_spam)
        url = reverse("comments-approve", args=[comment.id])
        response = self.c.post(url, follow=True)
        self.assertEqual(200, response.status_code)

        # reload the comment
        comment = MPTTComment.objects.get(id=comment.id)
        self.assertFalse(comment.is_spam)
        self.assertTrue(comment.is_public)

        # assert that the comment moderator sent a submit_ham message to Akismet
        post_args = AKISMET_POST_MOCK.post_args.pop()
        self.assertEqual(AKISMET_POST_MOCK.SUBMIT_HAM_PATH, post_args[2])

    def test_mark_as_spam_notifies_akismet(self):
        # make sure the logged in user has permissions to moderate comments (it's a superuser)
        login_successful = self.c.login(username=self.user.username, password="password")
        self.assertTrue(login_successful)

        comment = self._make_ham_comment()
        url = reverse("comments-mark-spam", args=[comment.id])
        response = self.c.post(url, follow=True)
        self.assertEqual(200, response.status_code)

        # reload the comment
        comment = MPTTComment.objects.get(id=comment.id)
        self.assertTrue(comment.is_spam)
        self.assertFalse(comment.is_public)

        # assert that the comment moderator sent a submit_spam message to Akismet
        post_args = AKISMET_POST_MOCK.post_args.pop()
        self.assertEqual(AKISMET_POST_MOCK.SUBMIT_SPAM_PATH, post_args[2])

    def test_removed_and_non_public_comments(self):
        post = create_post(author=self.author)
        comment1 = self._make_ham_comment(post, parent=None)
        comment1_1 = self._make_ham_comment(post, parent=comment1)
        comment1_1_1 = self._make_ham_comment(post, parent=comment1_1)
        comment2 = self._make_ham_comment(post, parent=None)

        response = self.c.get(post.get_absolute_url())
        self.assertEquals(200, response.status_code)
        comment_div = BeautifulSoup(response.content).select('div#comments')[0]
        self.assertIsNotNone(comment_div)
        root_comments = comment_div.ul.find_all('li', recursive=False)
        self.assertEqual(2, len(root_comments))

        self.assertEqual(comment1.comment, root_comments[0].div.text.strip())
        self.assertEqual(comment2.comment, root_comments[1].div.text.strip())

        # mark comment1 as 'removed'
        comment1 = MPTTComment.objects.get(pk=comment1.pk)
        comment1.is_removed = True
        comment1.full_clean()
        comment1.save()

        response = self.c.get(post.get_absolute_url())
        self.assertEquals(200, response.status_code)
        comment_div = BeautifulSoup(response.content).select('div#comments')[0]
        self.assertIsNotNone(comment_div)
        root_comments = comment_div.ul.find_all('li', recursive=False)
        self.assertEqual(2, len(root_comments))

        self.assertEqual("(Comment has been removed)", root_comments[0].div.text.strip())
        self.assertEqual(comment2.comment, root_comments[1].div.text.strip())

        # assert that the text of the replies to comment1 are still visible
        comment1_li = root_comments[0]
        self.assertIsNotNone(comment1_li.ul)
        self.assertEquals(comment1_1.comment, comment_div.li.ul.li.div.text.strip())
        self.assertEquals(comment1_1_1.comment, comment_div.li.ul.li.ul.li.div.text.strip())  # oh god

        # mark comment1 as 'non-public'
        comment1 = MPTTComment.objects.get(pk=comment1.pk)
        comment1.is_public = False
        comment1.full_clean()
        comment1.save()

        response = self.c.get(post.get_absolute_url())
        self.assertEquals(200, response.status_code)
        comment_div = BeautifulSoup(response.content).select('div#comments')[0]
        self.assertIsNotNone(comment_div)
        root_comments = comment_div.ul.find_all('li', recursive=False)

        # only comment2 should be visible, all children of comment1 should be hidden
        self.assertEqual(1, len(root_comments))
        self.assertEqual(comment2.comment, root_comments[0].div.text.strip())
        self.assertIsNone(root_comments[0].ul)  # no child comments

    def _make_spam_comment(self, post=None, **kwargs):
        if not post:
            post = create_post(author=self.author)

        num_comments = MPTTComment.objects.count()
        data = self.make_post_comment_data(post, **kwargs)
        url = comments_app.get_form_target()
        AKISMET_POST_MOCK.set_valid_key(True)
        AKISMET_POST_MOCK.set_comment_is_spam(True)

        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        comments = MPTTComment.objects.all()
        self.assertEqual(num_comments + 1, len(comments))
        comment = MPTTComment.objects.order_by('-submit_date')[0]
        self.assertTrue(comment.is_spam)
        self.assertFalse(comment.is_public)
        return comment

    def _make_ham_comment(self, post=None, **kwargs):
        if not post:
            post = create_post(author=self.author)

        num_comments = MPTTComment.objects.count()
        data = self.make_post_comment_data(post, **kwargs)
        url = comments_app.get_form_target()
        AKISMET_POST_MOCK.set_valid_key(True)
        AKISMET_POST_MOCK.set_comment_is_spam(False)

        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        comments = MPTTComment.objects.all()
        self.assertEqual(num_comments + 1, len(comments))
        comment = MPTTComment.objects.order_by('-submit_date')[0]
        self.assertFalse(comment.is_spam)
        self.assertTrue(comment.is_public)
        return comment

    def assert_comment_form_error(self, data, field_name, field_error, required=True):
        url = comments_app.get_form_target()
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertFormError(response, 'form', field_name, field_error)
        self.assertNotContains(response, "URL")  # url field should be hidden
        soup = BeautifulSoup(response.content)
        forms = soup.find_all('form', 'comment')  # shortcut to narrow by class=comment

        # there should be exactly one comment form on the page
        self.assertEqual(1, len(forms))
        form = forms[0]

        # the label corresponding to <field-name> should contain the error strings
        label = form.find('label', {'for': 'id_%s' % field_name})
        self.assertIsNotNone(label)

        # assert that there is a 'label' span
        self.assertIsNotNone(label.find('span', 'label'))

        if required:
            self.assertIsNotNone(label.find('span', 'required-text'))
        else:
            self.assertIsNotNone(label.find('span', 'optional-text'))

        # assert that there is an 'error' span that contains the expected error message fragment
        error_span = label.find('span', 'error')
        self.assertIsNotNone(error_span)
        self.assertTrue(field_error in error_span.get_text())


    def make_post_comment_data(self, post, **kwargs):
        timestamp = int(time.time())
        form = CommentSecurityForm(post)
        security_hash = form.initial_security_hash(timestamp)
        index = COUNTER.next()

        # make sure the comment field varies for each post, otherwise django will detect that the comments are
        # duplicates of each other and silently return the earlier comment
        data = {
            'name': kwargs.get('name', 'John Doe'),
            'email': kwargs.get('email', 'johndoe@fake.com'),
            'url': kwargs.get('url', ''),
            'comment': kwargs.get('comment', 'testing, testing %d' % index),
            'content_type': 'blog.post',
            'timestamp': timestamp,
            'object_pk': post.id,
            'security_hash': security_hash,
        }
        parent = kwargs.get('parent', None)

        if parent:
            data.update({'parent': parent._get_pk_val()})

        return data


class Counter():
    def __init__(self):
        self.n = 0

    def next(self):
        self.n += 1
        return self.n


COUNTER = Counter()


def make_consecutive_daily_posts(num, **kwargs):
    today = datetime.date.today()
    return [create_post(pub_date=(today - datetime.timedelta(x)), **kwargs) for x in xrange(num)]


def create_post(**kwargs):
    """
    Creates a blog posting using the given keyword arguments.  If a required field is not present in the keywords then
    a suitable default will be inserted.  As such, this method should not be used to test the 'requiredness' of a
    field.
    """
    index = COUNTER.next()
    title = kwargs.get('title', 'Some Title %d' % index)
    title_slug = kwargs.get('title_slug', 'some-title-%d' % index)
    author = kwargs.get('author', None)
    synopsis = kwargs.get('synopsis', 'Some synopsis.')
    body = kwargs.get('body', 'Some body text.')
    enable_comments = kwargs.get('enable_comments', True)
    is_draft = kwargs.get('is_draft', False)
    tags = kwargs.get('tags', [])

    post = Post(title=title, title_slug=title_slug, author=author, synopsis=synopsis, body=body,
                enable_comments=enable_comments, is_draft=is_draft)

    post.full_clean()
    post.save()

    needs_another_save = False

    for tag in tags:
        post.tags.add(tag)
        needs_another_save = True

    if 'pub_date' in kwargs:
        post.pub_date = kwargs['pub_date']
        needs_another_save = True

    if needs_another_save:
        post.full_clean()
        post.save()

    return post

