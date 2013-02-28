from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import AuthorProfile, Post
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from blog import validators
from django.test.client import Client
import datetime
from monthdelta import MonthDelta

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
        post = self.create_post(title="Why I Wear Yoga Pants", title_slug="slug", author=self.author, body="hi")
        self.assertIsNotNone(post.pub_date)
        self.assertIsNotNone(post.mod_date)
        self.assertEqual(post.pub_date, post.mod_date)
        self.assertEqual(self.author.pen_name, post.get_author_name())
        self.assertEqual(self.user.email, post.get_author_email())

    def test_create_post_title_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title=blank, title_slug="whatever", author=self.author, body="hi")
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_slug_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title="whatever", title_slug=blank, author=self.author, body="hi")
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_body_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title="whatever", title_slug="whatever", author=self.author, body=blank)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_duplicate_titles_allowed(self):
        title = "Hello, I am a title."
        # as long as the slugs are different this should be allowed
        self.create_post(title=title, title_slug="slug1", author=self.author, body="body")
        self.create_post(title=title, title_slug="slug2", author=self.author, body="body")

    def test_duplicate_slugs_not_allowed(self):
        slug = "slug"
        self.create_post(title="title", title_slug=slug, author=self.author, body="body")
        with self.assertRaises(ValidationError) as cm:
            self.create_post(title="new title", title_slug=slug, author=self.author, body="body")
        self.assertIn("title_slug", str(cm.exception))

    def test_get_url(self):
        title = "Why I Love Yoga Pants"
        title_slug = "why-i-love-yoga-pants"
        body = "some meaningless text"
        post = self.create_post(title=title, title_slug=title_slug, author=self.author, body=body)
        url = post.get_url()

        # check that the url is sane
        c = Client()
        response = c.get(url)
        self.assertEqual(200, response.status_code)

    def create_post(self, *args, **kwargs):
        post = Post(*args, **kwargs)
        post.full_clean()
        post.save()
        return post


#-----------------------------
# VIEW TESTS
#-----------------------------

class GenericArchiveViewTests(TestCase):

    def setUp(self):
        self.c = Client()
        self.n = 1
        self.user = User(username="arthur", password="whocares", email="me@example.com")
        self.user.full_clean()
        self.user.save()
        self.author = AuthorProfile(user=self.user, pen_name="Captain Yoga Pants")
        self.author.full_clean()
        self.author.save()

    def test_archive_templates_used(self):
        today = datetime.date.today()
        self.create_post(today)

        response = self.c.get(self.get_archive_url(today))
        self.assertTemplateUsed(response, "blog/post_archive.html")

        response = self.c.get(self.get_archive_url(today, 'year'))
        self.assertTemplateUsed(response, "blog/post_archive_year.html")

        response = self.c.get(self.get_archive_url(today, 'month'))
        self.assertTemplateUsed(response, "blog/post_archive_month.html")

        response = self.c.get(self.get_archive_url(today, 'day'))
        self.assertTemplateUsed(response, "blog/post_archive_day.html")

    def test_empty_views_allowed(self):
        # we don't want archive views with no posts to throw 404
        posts = Post.objects.all()
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

        post = self.create_post(post_date)

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

    def test_post_detail_view(self):
        post_date = datetime.date.today()
        post = self.create_post(post_date)
        response = self.c.get(post.get_url())
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, post.title)
        self.assertContains(response, post.get_author_name())
        self.assert_contains_link(response, self.get_archive_url())

        bogus_url = post.get_url().rstrip("/") + "garbage/"
        response = self.c.get(bogus_url)
        self.assertEqual(404, response.status_code)

    def assert_post_in_archive(self, date, post, level='all'):
        url = self.get_archive_url(date, level)
        response = self.c.get(url)
        self.assertContains(response, post.title)
        self.verify_generic_archive_properties(response, date=date, level=level)

    def assert_post_not_in_archive(self, date, post, level='all'):
        url = self.get_archive_url(date, level)
        response = self.c.get(url)
        self.assertNotContains(response, post.title)
        self.verify_generic_archive_properties(response, date=date, level=level)

    def assert_contains_link(self, response, url, count=None):
        fragment = "href=\"%s\"" % url
        self.assertContains(response, fragment, count=count)

    def verify_generic_archive_properties(self, response, date=None, level='all'):
        # all pages should have a link to the archives in the footer
        self.assert_contains_link(response, self.get_archive_url())

        if level in ['all', 'year']:
            return
        today = datetime.date.today()

        if level == 'month':
            previous_month = date + MonthDelta(-1)
            self.assert_contains_link(response, self.get_archive_url(date=previous_month, level='month'))
            next_month = date + MonthDelta(+1)
            next_month.replace(next_month.year, next_month.month, 1)
            # make sure it isn't a future month
            if next_month <= today:
                self.assert_contains_link(response, self.get_archive_url(date=next_month, level='month'))

        elif level == 'day':
            previous_day = date - datetime.timedelta(1)
            self.assert_contains_link(response, self.get_archive_url(date=previous_day, level='day'))
            next_day = date + datetime.timedelta(1)
            # make sure it isn't a future day
            if next_day <= today:
                self.assert_contains_link(response, self.get_archive_url(date=next_day, level='day'))

    def create_post(self, date):
        title = "title %d" % self.n
        slug = "title_slug_%d" % self.n
        body = "some text"
        post = Post(body=body, title=title, title_slug=slug, author=self.author)
        post.full_clean()
        post.save()
        # hack to bypass the auto_now_add=True behaviour of pub_date
        post.pub_date = date
        post.save()
        self.n += 1
        return post

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

