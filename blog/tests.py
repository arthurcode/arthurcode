from django.test import TestCase
from django.contrib.auth.models import User
from blog.models import AuthorProfile, Post
from django.core.exceptions import ValidationError
from blog import validators

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


    def create_post(self, *args, **kwargs):
        post = Post(*args, **kwargs)
        post.full_clean()
        post.save()
        return post
