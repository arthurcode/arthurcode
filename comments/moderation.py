"""
A generic comment-moderation system which allows configuration of
moderation options on a per-model basis.

To use, do two things:

1. Create or import a subclass of ``CommentModerator`` defining the
   options you want.

2. Import ``moderator`` from this module and register one or more
   models, passing the models and the ``CommentModerator`` options
   class you want to use.


Example
-------

First, we define a simple model class which might represent entries in
a Weblog::

    from django.db import models

    class Entry(models.Model):
        title = models.CharField(maxlength=250)
        body = models.TextField()
        pub_date = models.DateField()
        enable_comments = models.BooleanField()

Then we create a ``CommentModerator`` subclass specifying some
moderation options::

    from django.contrib.comments.moderation import CommentModerator, moderator

    class EntryModerator(CommentModerator):
        email_notification = True
        enable_field = 'enable_comments'

And finally register it for moderation::

    moderator.register(Entry, EntryModerator)

This sample class would apply two moderation steps to each new
comment submitted on an Entry:

* If the entry's ``enable_comments`` field is set to ``False``, the
  comment will be rejected (immediately deleted).

* If the comment is successfully posted, an email notification of the
  comment will be sent to site staff.

For a full list of built-in moderation options and other
configurability, see the documentation for the ``CommentModerator``
class.

"""

import datetime

from django.conf import settings
from django.core.mail import send_mail
from comments import signals
from django.db.models.base import ModelBase
from django.template import Context, loader
import comments
from django.contrib.sites.models import Site
from django.utils import timezone
from akismet import AkismetError, verify_key, comment_check, submit_ham, submit_spam


class AlreadyModerated(Exception):
    """
    Raised when a model which is already registered for moderation is
    attempting to be registered again.

    """
    pass

class NotModerated(Exception):
    """
    Raised when a model which is not registered for moderation is
    attempting to be unregistered.

    """
    pass

class CommentModerator(object):
    """
    Encapsulates comment-moderation options for a given model.

    This class is not designed to be used directly, since it doesn't
    enable any of the available moderation options. Instead, subclass
    it and override attributes to enable different options::

    ``auto_close_field``
        If this is set to the name of a ``DateField`` or
        ``DateTimeField`` on the model for which comments are
        being moderated, new comments for objects of that model
        will be disallowed (immediately deleted) when a certain
        number of days have passed after the date specified in
        that field. Must be used in conjunction with
        ``close_after``, which specifies the number of days past
        which comments should be disallowed. Default value is
        ``None``.

    ``auto_moderate_field``
        Like ``auto_close_field``, but instead of outright
        deleting new comments when the requisite number of days
        have elapsed, it will simply set the ``is_public`` field
        of new comments to ``False`` before saving them. Must be
        used in conjunction with ``moderate_after``, which
        specifies the number of days past which comments should be
        moderated. Default value is ``None``.

    ``close_after``
        If ``auto_close_field`` is used, this must specify the
        number of days past the value of the field specified by
        ``auto_close_field`` after which new comments for an
        object should be disallowed. Default value is ``None``.

    ``email_notification``
        If ``True``, any new comment on an object of this model
        which survives moderation will generate an email to site
        staff. Default value is ``False``.

    ``enable_field``
        If this is set to the name of a ``BooleanField`` on the
        model for which comments are being moderated, new comments
        on objects of that model will be disallowed (immediately
        deleted) whenever the value of that field is ``False`` on
        the object the comment would be attached to. Default value
        is ``None``.

    ``moderate_after``
        If ``auto_moderate_field`` is used, this must specify the number
        of days past the value of the field specified by
        ``auto_moderate_field`` after which new comments for an
        object should be marked non-public. Default value is
        ``None``.

    Most common moderation needs can be covered by changing these
    attributes, but further customization can be obtained by
    subclassing and overriding the following methods. Each method will
    be called with three arguments: ``comment``, which is the comment
    being submitted, ``content_object``, which is the object the
    comment will be attached to, and ``request``, which is the
    ``HttpRequest`` in which the comment is being submitted::

    ``allow``
        Should return ``True`` if the comment should be allowed to
        post on the content object, and ``False`` otherwise (in
        which case the comment will be immediately deleted).

    ``email``
        If email notification of the new comment should be sent to
        site staff or moderators, this method is responsible for
        sending the email.

    ``moderate``
        Should return ``True`` if the comment should be moderated
        (in which case its ``is_public`` field will be set to
        ``False`` before saving), and ``False`` otherwise (in
        which case the ``is_public`` field will not be changed).

    Subclasses which want to introspect the model for which comments
    are being moderated can do so through the attribute ``_model``,
    which will be the model class.

    """
    auto_close_field = None
    auto_moderate_field = None
    close_after = None
    email_notification = False
    enable_field = None
    moderate_after = None

    def __init__(self, model):
        self._model = model

    def _get_delta(self, now, then):
        """
        Internal helper which will return a ``datetime.timedelta``
        representing the time between ``now`` and ``then``. Assumes
        ``now`` is a ``datetime.date`` or ``datetime.datetime`` later
        than ``then``.

        If ``now`` and ``then`` are not of the same type due to one of
        them being a ``datetime.date`` and the other being a
        ``datetime.datetime``, both will be coerced to
        ``datetime.date`` before calculating the delta.

        """
        if now.__class__ is not then.__class__:
            now = datetime.date(now.year, now.month, now.day)
            then = datetime.date(then.year, then.month, then.day)
        if now < then:
            raise ValueError("Cannot determine moderation rules because date field is set to a value in the future")
        return now - then

    def allow(self, comment, content_object, request):
        """
        Determine whether a given comment is allowed to be posted on
        a given object.

        Return ``True`` if the comment should be allowed, ``False
        otherwise.

        """
        if self.enable_field:
            if not getattr(content_object, self.enable_field):
                return False
        if self.auto_close_field and self.close_after is not None:
            close_after_date = getattr(content_object, self.auto_close_field)
            if close_after_date is not None and self._get_delta(timezone.now(), close_after_date).days >= self.close_after:
                return False
        return True

    def moderate(self, comment, content_object, request):
        """
        Determine whether a given comment on a given object should be
        allowed to show up immediately, or should be marked non-public
        and await approval.

        Return ``True`` if the comment should be moderated (marked
        non-public), ``False`` otherwise.

        """
        if self.auto_moderate_field and self.moderate_after is not None:
            moderate_after_date = getattr(content_object, self.auto_moderate_field)
            if moderate_after_date is not None and self._get_delta(timezone.now(), moderate_after_date).days >= self.moderate_after:
                return True
        if self.check_spam(comment, content_object, request):
            comment.is_spam = True
            return True
        return False

    def email(self, comment, content_object, request):
        """
        Send email notification of a new comment to site staff and comment authors when a new
        comment/reply is posted.

        Returns the list of recipients to whom an email notification was sent.
        """
        if not self.email_notification:
            return []

        recipient_list = [manager_tuple[1] for manager_tuple in settings.MANAGERS]
        subject = '[%s] New comment posted on "%s"' % (Site.objects.get_current().name,
                                                       content_object)
        self._send_email(comment, content_object, 'comments/email_new_comment.html', subject, recipient_list)

        if comment.is_public and hasattr(comment, 'parent'):
            recipient_list.extend(self._email_comment_parent(comment, content_object, request))
            recipient_list.extend(self._email_comment_ancestors(comment, content_object, request))
        return recipient_list

    def _email_comment_parent(self, comment, content_object, request):
        recipient_list = []

        if comment.parent and \
                comment.parent.user_email and \
                comment.parent.email_on_reply and \
                comment.parent.user_email != comment.user_email:
            recipient_list.append(comment.parent.user_email)

        subject = '[%s] %s replied to your comment on "%s"' % (Site.objects.get_current().name,
                                                               comment.user_name, content_object)
        self._send_email(comment, content_object, 'comments/email_new_comment.html', subject, recipient_list)
        return recipient_list

    def _email_comment_ancestors(self, comment, content_object, request):
        if not comment.parent:
            return []

        ancestors = comment.parent.get_ancestors(include_self=False)
        recipient_list = set()
        subject = '[%s] %s replied to your comment thread on "%s"' % (Site.objects.get_current().name,
                                                                      comment.user_name, content_object)

        for ancestor in ancestors:
            if ancestor.email_on_reply and ancestor.user_email and ancestor.user_email not in [comment.parent.user_email, comment.user_email]:
                recipient_list.add(ancestor.user_email)

        for recipient in recipient_list:
            # we don't want the comment authors to see the email addresses of the other comment authors
            self._send_email(comment, content_object, 'comments/email_new_comment.html', subject, [recipient])
        return recipient_list

    def _send_email(self, comment, content_object, template, subject, recipient_list):
        if not recipient_list:
            return
        t = loader.get_template(template)
        c = Context({ 'comment': comment,
                      'content_object': content_object,
                      'recipients': recipient_list})
        message = t.render(c)
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=True)

    def check_spam(self, comment, content_object, request):
        return False

    def marked_as_spam(self, comment, request):
        pass

    def marked_not_spam(self, comment, request):
        pass


class AkismetCommentModerator(CommentModerator):
    """ Checks for comment spam using the Akismet API.

    Expects there to be an AKISMET_KEY variable in settings.py.
    """

    def check_spam(self, comment, content_object, request):
        """
        Returns True if the comment is spam and False if it's ham.
        """
        key = self._get_key()

        if not key:
            # TODO: log a warning
            return False

        try:
            if verify_key(key, comment.site.domain):
                data = self._get_data_from_comment(comment)
                data.update({
                    # not stored on the comment model, have to get them from the request
                    'referrer': request.META.get('HTTP_REFERER', ''),
                    'user_agent': request.META.get('HTTP_USER_AGENT', '')
                })
                return comment_check(key, comment.site.domain, **data)
        except AkismetError, e:
            # TODO: log a warning with the exception
            print e.response, e.statuscode
        return False

    def marked_as_spam(self, comment, request):
        key = self._get_key()
        if not key:
            return

        try:
            if verify_key(key, comment.site.domain):
                data = self._get_data_from_comment(comment)
                submit_spam(key, comment.site.domain, **data)
        except AkismetError, e:
            print e.response, e.statuscode

    def marked_not_spam(self, comment, request):
        key = self._get_key()
        if not key:
            return

        try:
            if verify_key(key, comment.site.domain):
                data = self._get_data_from_comment(comment)
                submit_ham(key, comment.site.domain, **data)
        except AkismetError, e:
            print e.response, e.statuscode

    def _get_key(self):
        return getattr(settings, 'AKISMET_KEY', None)

    def _get_data_from_comment(self, comment):
        data = {
            'comment_type': 'comment',
            'comment_author': comment.user_name.encode('utf-8'),
            'comment_author_email': comment.user_email.encode('utf-8'),
            'comment_content': comment.comment.encode('utf-8'),
            'user_ip': unicode(comment.ip_address or ''),
            'user_agent': '',
        }

        if comment.user_url:
            data.update('comment_author_url', comment.user_url.encode('utf-8'))

        return data

class Moderator(object):
    """
    Handles moderation of a set of models.

    An instance of this class will maintain a list of one or more
    models registered for comment moderation, and their associated
    moderation classes, and apply moderation to all incoming comments.

    To register a model, obtain an instance of ``Moderator`` (this
    module exports one as ``moderator``), and call its ``register``
    method, passing the model class and a moderation class (which
    should be a subclass of ``CommentModerator``). Note that both of
    these should be the actual classes, not instances of the classes.

    To cease moderation for a model, call the ``unregister`` method,
    passing the model class.

    For convenience, both ``register`` and ``unregister`` can also
    accept a list of model classes in place of a single model; this
    allows easier registration of multiple models with the same
    ``CommentModerator`` class.

    The actual moderation is applied in two phases: one prior to
    saving a new comment, and the other immediately after saving. The
    pre-save moderation may mark a comment as non-public or mark it to
    be removed; the post-save moderation may delete a comment which
    was disallowed (there is currently no way to prevent the comment
    being saved once before removal) and, if the comment is still
    around, will send any notification emails the comment generated.

    """
    def __init__(self):
        self._registry = {}
        self.connect()

    def connect(self):
        """
        Hook up the moderation methods to pre- and post-save signals
        from the comment models.

        """
        signals.comment_will_be_posted.connect(self.pre_save_moderation, sender=comments.get_model())
        signals.comment_was_posted.connect(self.post_save_moderation, sender=comments.get_model())
        signals.comment_was_marked_as_spam.connect(self.marked_as_spam_moderation, sender=comments.get_model())
        signals.comment_was_marked_not_spam.connect(self.marked_not_spam_moderation, sender=comments.get_model())

    def register(self, model_or_iterable, moderation_class):
        """
        Register a model or a list of models for comment moderation,
        using a particular moderation class.

        Raise ``AlreadyModerated`` if any of the models are already
        registered.

        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model in self._registry:
                raise AlreadyModerated("The model '%s' is already being moderated" % model._meta.module_name)
            self._registry[model] = moderation_class(model)

    def unregister(self, model_or_iterable):
        """
        Remove a model or a list of models from the list of models
        whose comments will be moderated.

        Raise ``NotModerated`` if any of the models are not currently
        registered for moderation.

        """
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                raise NotModerated("The model '%s' is not currently being moderated" % model._meta.module_name)
            del self._registry[model]

    def pre_save_moderation(self, sender, comment, request, **kwargs):
        """
        Apply any necessary pre-save moderation steps to new
        comments.

        """
        model = comment.content_type.model_class()
        if model not in self._registry:
            return
        content_object = comment.content_object
        moderation_class = self._registry[model]

        # Comment will be disallowed outright (HTTP 403 response)
        if not moderation_class.allow(comment, content_object, request): 
            return False

        if moderation_class.moderate(comment, content_object, request):
            comment.is_public = False

    def post_save_moderation(self, sender, comment, request, **kwargs):
        """
        Apply any necessary post-save moderation steps to new
        comments.

        """
        model = comment.content_type.model_class()
        if model not in self._registry:
            return
        self._registry[model].email(comment, comment.content_object, request)

    def marked_as_spam_moderation(self, sender, comment, request, **kwargs):
        model = comment.content_type.model_class()
        if model not in self._registry:
            return
        self._registry[model].marked_as_spam(comment, request)

    def marked_not_spam_moderation(self, sender, comment, request, **kwargs):
        model = comment.content_type.model_class()
        if model not in self._registry:
            return
        self._registry[model].marked_not_spam(comment, request)

# Import this instance in your own code to use in registering
# your models for moderation.
moderator = Moderator()
