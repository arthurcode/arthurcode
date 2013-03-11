from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import AuthorProfile, Post
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.core.urlresolvers import reverse
from blog import validators
from django.test.client import Client
import datetime, time
from monthdelta import MonthDelta
from comments.forms import MPTTCommentForm
from comments.models import MPTTComment
import django.contrib.comments as django_comments
from django.contrib.comments.forms import CommentSecurityForm

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
        post = self.create_post(title="Why I Wear Yoga Pants", title_slug="slug", author=self.author, body="hi",
                                synopsis="some synopsis")
        self.assertIsNotNone(post.pub_date)
        self.assertIsNotNone(post.mod_date)
        self.assertEqual(post.pub_date, post.mod_date)
        self.assertEqual(self.author.pen_name, post.get_author_name())
        self.assertEqual(self.user.email, post.get_author_email())

    def test_create_post_title_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title=blank, title_slug="whatever", author=self.author, body="hi", synopsis="whatever")
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_slug_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title="whatever", title_slug=blank, author=self.author, body="hi", synopsis="whatever")
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_body_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title="whatever", title_slug="whatever", author=self.author, body=blank, synopsis="whatever")
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_create_post_synopsis_cannot_be_blank(self):
        for blank in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                self.create_post(title="whatever", title_slug="whatever", author=self.author, body="whatever", synopsis=blank)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def test_duplicate_titles_allowed(self):
        title = "Hello, I am a title."
        # as long as the slugs are different this should be allowed
        self.create_post(title=title, title_slug="slug1", author=self.author, body="body", synopsis="whatever")
        self.create_post(title=title, title_slug="slug2", author=self.author, body="body", synopsis="whatever")

    def test_duplicate_slugs_not_allowed(self):
        slug = "slug"
        self.create_post(title="title", title_slug=slug, author=self.author, body="body", synopsis="whatever")
        with self.assertRaises(ValidationError) as cm:
            self.create_post(title="new title", title_slug=slug, author=self.author, body="body", synopsis="whatever")
        self.assertIn("title_slug", str(cm.exception))

    def test_get_absolute_url(self):
        title = "Why I Love Yoga Pants"
        title_slug = "why-i-love-yoga-pants"
        body = "some meaningless text"
        synopsis = "whatever"
        post = self.create_post(title=title, title_slug=title_slug, author=self.author, body=body, synopsis=synopsis)
        url = post.get_absolute_url()

        # check that the url is sane
        c = Client()
        response = c.get(url)
        self.assertEqual(200, response.status_code)

    def test_comments_enabled(self):
        title = "Who Cares?"
        title_slug = "not-me"
        body = "some text"
        synopsis = "whatever"
        post = self.create_post(title=title, title_slug=title_slug, author=self.author, body=body, synopsis=synopsis)
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

    def test_archive_multiple_posts(self):
        post_date_1 = datetime.date(2011, 8, 23)
        post_date_2 = datetime.date(2013, 1, 1)

        post_1 = self.create_post(post_date_1)
        post_2 = self.create_post(post_date_2)
        self.assert_post_in_archive(post_date_1, post_1, level='all')
        self.assert_post_in_archive(post_date_2, post_2, level='all')

    def test_post_detail_view(self):
        post_date = datetime.date.today()
        post = self.create_post(post_date)
        response = self.c.get(post.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, post.title)
        self.assertContains(response, post.get_author_name())
        self.assert_contains_link(response, self.get_archive_url())
        self.assert_does_not_contain_link(response, post.get_absolute_url())
        self.assertNotContains(response, "last-modified")

        post_date = datetime.date.today() - datetime.timedelta(1)
        post = self.create_post(post_date)
        response = self.c.get(post.get_absolute_url())
        # last modified will default to today's date, which is one day later than the publication date
        self.assertContains(response, "last-modified")

        bogus_url = post.get_absolute_url().rstrip("/") + "garbage/"
        response = self.c.get(bogus_url)
        self.assertEqual(404, response.status_code)

    def test_index(self):
        # test that we don't die a horrible death when the index is rendered when there are no posts in the database
        response = self.c.get(reverse('index'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assertContains(response, "No post")

        post_1 = self.create_post(datetime.date(2013, 01, 02))
        post_2 = self.create_post(datetime.date(2013, 01, 03))
        response = self.c.get(reverse('index'))
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, "blog/post_detail.html")
        self.assert_contains_link(response, reverse('index'))

        # assert that only the latest post is rendered on the main page, and that there is a permalink to the post's url
        self.assertContains(response, post_2.title)
        self.assertNotContains(response, post_1.title)
        self.assert_contains_link(response, post_2.get_absolute_url())
        self.assert_does_not_contain_link(response, post_1.get_absolute_url())
        self.assert_contains_link(response, reverse('index'))

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

    def verify_generic_archive_properties(self, response, date=None, level='all'):
        # all pages should have a link to the archives in the footer
        self.assert_contains_link(response, self.get_archive_url())
        # all pages should have a link to the main blog page
        self.assert_contains_link(response, reverse('index'))

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
        synopsis = "some synopsis"
        post = Post(body=body, title=title, title_slug=slug, author=self.author, synopsis=synopsis)
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


class CommentingTest(TestCase):

    def setUp(self):
        self.c = Client()
        self.n = 1
        self.user = User.objects.create_user("username", "someone@fake.com", "password")
        self.author = AuthorProfile(user=self.user, pen_name="Captain Yoga Pants")
        self.author.full_clean()
        self.author.save()

    def test_use_mptt_comments(self):
        """
        Test that we have properly customized the built-in comments app.
        """
        self.assertEqual(MPTTComment, django_comments.get_model())
        self.assertEqual(MPTTCommentForm, django_comments.get_form())

    def test_post_comments(self):
        post = self.create_post()
        data = self.make_post_comment_data(post, parent=None)
        url = django_comments.get_form_target()
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
        post = self.create_post(enable_comments=False)
        data = self.make_post_comment_data(post, parent=None)
        url = django_comments.get_form_target()
        response = self.c.post(url, data, follow=True)
        self.assertEqual(400, response.status_code)
        self.assertEqual(0, MPTTComment.objects.all().count())

        post.enable_comments = True
        post.save()
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, MPTTComment.objects.all().count())

    def make_post_comment_data(self, post, parent=None):
        timestamp = int(time.time())
        form = CommentSecurityForm(post)
        security_hash = form.initial_security_hash(timestamp)

        # make sure the comment field varies for each post, otherwise django will detect that the comments are
        # duplicates of each other and silently return the earlier comment
        data = {
            'name': 'John Doe',
            'email': 'johndoe@fake.com',
            'url': '',
            'comment': 'testing, testing %d' % self.n,
            'content_type': 'blog.post',
            'timestamp': timestamp,
            'object_pk': post.id,
            'security_hash': security_hash,
        }

        if parent:
            data.update({'parent': parent._get_pk_val()})

        self.n += 1
        return data

    def create_post(self, enable_comments=True):
        title = "title %d" % self.n
        title_slug = "title-%d" % self.n
        post = Post(title=title, title_slug=title_slug, author=self.author, body="text", enable_comments=enable_comments,
                    synopsis="whatever")
        post.full_clean()
        post.save()
        self.n += 1
        return post

