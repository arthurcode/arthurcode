from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from comments.moderation import AkismetCommentModerator, moderator
from utils import is_blank
from validators import not_blank
import datetime
from taggit.managers import TaggableManager
from taggit.models import TaggedItemBase


class AuthorProfile(models.Model):
    """
    Each registered User may have zero or more author profiles.  An author profile defines a pen name that will be used
    to sign blog posts.  An author's pen name must be be unique.
    """
    ERROR_CREATE_NO_EMAIL = "The associated user's e-mail address cannot be blank."
    ERROR_CREATE_NO_FIRST_LAST_NAME = "Could not generate a default pen name because the user's first-name and/or \
                                   last-name is blank.  Please either specify the author's pen name or specify the \
                                   user's first and last name."

    user = models.ForeignKey(User)

    pen_name = models.CharField(max_length=100,
                                help_text="The name under which you will author blog postings.  If left blank it \
                                           will default to 'first-name last-name'.",
                                null=False,
                                blank=True,
                                unique=True)

    def clean(self, *args, **kwargs):
        self._validate_email()
        self._validate_pen_name()

    def _validate_email(self):
        # The user field, even though it's required, can still be undefined at the point this code is executed.  Check
        # for a user_id == None; checking for user == None doesn't seem to work properly. No doubt it has something to
        # do with django not being able to build the model instance
        if self.user_id and is_blank(self.user.email):
            raise ValidationError(AuthorProfile.ERROR_CREATE_NO_EMAIL)

    def _validate_pen_name(self):
        """
         If the pen_name is blank a default of '<first-name> <last-name>' will be used.  If the user's first-name
         and/or last-name are blank a ValidationError will be raised.
        """
        if not is_blank(self.pen_name):
            return
        if is_blank(self.user.first_name) or is_blank(self.user.last_name):
            raise ValidationError(AuthorProfile.ERROR_CREATE_NO_FIRST_LAST_NAME)
        self.pen_name = "%s %s" % (self.user.first_name, self.user.last_name)

    def __unicode__(self):
        return self.pen_name


class TaggedPost(TaggedItemBase):
    """
    A custom tag for Posts.  Since I'll only be tagging posts it's a little more efficient to use a ForeignKey
    relationship rather than a generic Foreign key: http://django-taggit.readthedocs.org/en/latest/custom_tagging.html
    """
    content_object = models.ForeignKey('Post')


class PublishedPostManager(models.Manager):
    def get_query_set(self):
        return super(PublishedPostManager, self).get_query_set().filter(is_draft=False)


class Post(models.Model):
    TITLE_MAX_LENGTH = 200

    objects = models.Manager()
    published = PublishedPostManager()
    tags = TaggableManager(through=TaggedPost)

    author = models.ForeignKey(AuthorProfile)

    title = models.CharField(max_length=TITLE_MAX_LENGTH,
                             validators=[not_blank])

    # I originally wanted to use 'unique_for_date' to enforce that the title slug need only be unique for the
    # publication date.  However, since this field is not edited on the admin form the dual-field uniqueness constraint
    # was not being run by django when a post was added through the admin interface.  This type of constraint isn't
    # enforced by the database, so the effect was that this condition was being effectively ignored.  This is
    # django bug 13091.  Switch to using unique=True.
    title_slug = models.SlugField(max_length=TITLE_MAX_LENGTH,
                                  unique=True,
                                  verbose_name="title for URLs",
                                  validators=[not_blank])

    synopsis = models.CharField(max_length=1000,
                                validators=[not_blank],
                                help_text="A few sentences summarizing this post.  Google may display this summary,"
                                          " so put some effort into it.")

    pub_date = models.DateField(auto_now_add=True,
                                null=False,
                                verbose_name="publication date")

    mod_date = models.DateField(auto_now=True, verbose_name="last-modified date")
    body = models.TextField(help_text="The text of this blog post",
                            validators=[not_blank])

    enable_comments = models.BooleanField(default=True)

    is_draft = models.BooleanField(default=True)

    def get_author_name(self):
        return self.author.pen_name

    def get_author_email(self):
        return self.author.user.email

    def get_absolute_url(self):
        params = {
            'year': self.pub_date.year,
            'month': self.pub_date.month,
            'day': self.pub_date.day,
            'slug': self.title_slug
        }
        if self.is_draft:
            view_name = "draft_post_detail"
        else:
            view_name = "post_detail"
        return reverse(view_name, kwargs=params)

    def is_commenting_enabled(self):
        """
        Returns True if commenting is permitted on this post.  At this moment this simply returns the value of
        the 'enable_comments' field, but in the future the calculation may become more complex.
        """
        return self.enable_comments

    def publish(self):
        if self.is_draft:
            today = datetime.date.today()
            self.pub_date = today
            self.mod_date = today
            self.is_draft = False
            self.save()

    def __unicode__(self):
        return self.title


class PostModerator(AkismetCommentModerator):
    email_notification = False
    enable_field = 'enable_comments'


moderator.register(Post, PostModerator)

