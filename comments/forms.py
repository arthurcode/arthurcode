__author__ = 'rhyanarthur'

from django import forms
from django.contrib.comments.forms import CommentForm
from django.forms.widgets import HiddenInput
import time
from django.forms.util import ErrorDict
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from comments.models import Comment, MPTTComment
from django.utils.crypto import salted_hmac, constant_time_compare
from django.utils.encoding import force_unicode
from django.utils.text import get_text_list
from django.utils import timezone
from django.utils.translation import ungettext, ugettext, ugettext_lazy as _
from django.core.exceptions import ValidationError
from accounts.forms import DEFAULT_EMAIL_WIDGET

COMMENT_MAX_LENGTH = getattr(settings,'COMMENT_MAX_LENGTH', 3000)

class CommentSecurityForm(forms.Form):
    """
    Handles the security aspects (anti-spoofing) for comment forms.
    """
    content_type  = forms.CharField(widget=forms.HiddenInput)
    object_pk     = forms.CharField(widget=forms.HiddenInput)
    timestamp     = forms.IntegerField(widget=forms.HiddenInput)
    security_hash = forms.CharField(min_length=40, max_length=40, widget=forms.HiddenInput)

    def __init__(self, target_object, data=None, initial=None):
        self.target_object = target_object
        if initial is None:
            initial = {}
        initial.update(self.generate_security_data())
        super(CommentSecurityForm, self).__init__(data=data, initial=initial)

    def security_errors(self):
        """Return just those errors associated with security"""
        errors = ErrorDict()
        for f in ["honeypot", "timestamp", "security_hash"]:
            if f in self.errors:
                errors[f] = self.errors[f]
        return errors

    def clean_security_hash(self):
        """Check the security hash."""
        security_hash_dict = {
            'content_type' : self.data.get("content_type", ""),
            'object_pk' : self.data.get("object_pk", ""),
            'timestamp' : self.data.get("timestamp", ""),
            }
        expected_hash = self.generate_security_hash(**security_hash_dict)
        actual_hash = self.cleaned_data["security_hash"]
        if not constant_time_compare(expected_hash, actual_hash):
            raise forms.ValidationError("Security hash check failed.")
        return actual_hash

    def clean_timestamp(self):
        """Make sure the timestamp isn't too far (> 2 hours) in the past."""
        ts = self.cleaned_data["timestamp"]
        if time.time() - ts > (2 * 60 * 60):
            raise forms.ValidationError("Timestamp check failed")
        return ts

    def generate_security_data(self):
        """Generate a dict of security data for "initial" data."""
        timestamp = int(time.time())
        security_dict =   {
            'content_type'  : str(self.target_object._meta),
            'object_pk'     : str(self.target_object._get_pk_val()),
            'timestamp'     : str(timestamp),
            'security_hash' : self.initial_security_hash(timestamp),
            }
        return security_dict

    def initial_security_hash(self, timestamp):
        """
        Generate the initial security hash from self.content_object
        and a (unix) timestamp.
        """

        initial_security_dict = {
            'content_type' : str(self.target_object._meta),
            'object_pk' : str(self.target_object._get_pk_val()),
            'timestamp' : str(timestamp),
            }
        return self.generate_security_hash(**initial_security_dict)

    def generate_security_hash(self, content_type, object_pk, timestamp):
        """
        Generate a HMAC security hash from the provided info.
        """
        info = (content_type, object_pk, timestamp)
        key_salt = "django.contrib.forms.CommentSecurityForm"
        value = "-".join(info)
        return salted_hmac(key_salt, value).hexdigest()

class CommentDetailsForm(CommentSecurityForm):
    """
    Handles the specific details of the comment (name, comment, etc.).
    """
    name          = forms.CharField(label=_("Name"), max_length=50)
    email         = forms.EmailField(label=_("Email address"), required=False)
    url           = forms.URLField(label=_("URL"), required=False)
    comment       = forms.CharField(label=_('Comment'), widget=forms.Textarea,
                                    max_length=COMMENT_MAX_LENGTH)

    def get_comment_object(self):
        """
        Return a new (unsaved) comment object based on the information in this
        form. Assumes that the form is already validated and will throw a
        ValueError if not.

        Does not set any of the fields that would come from a Request object
        (i.e. ``user`` or ``ip_address``).
        """
        if not self.is_valid():
            raise ValueError("get_comment_object may only be called on valid forms")

        CommentModel = self.get_comment_model()
        new = CommentModel(**self.get_comment_create_data())
        new = self.check_for_duplicate_comment(new)

        return new

    def get_comment_model(self):
        """
        Get the comment model to create with this form. Subclasses in custom
        comment apps should override this, get_comment_create_data, and perhaps
        check_for_duplicate_comment to provide custom comment models.
        """
        return Comment

    def get_comment_create_data(self):
        """
        Returns the dict of data to be used to create a comment. Subclasses in
        custom comment apps that override get_comment_model can override this
        method to add extra fields onto a custom comment model.
        """
        return dict(
            content_type = ContentType.objects.get_for_model(self.target_object),
            object_pk    = force_unicode(self.target_object._get_pk_val()),
            user_name    = self.cleaned_data["name"],
            user_email   = self.cleaned_data["email"],
            user_url     = self.cleaned_data["url"],
            comment      = self.cleaned_data["comment"],
            submit_date  = timezone.now(),
            site_id      = settings.SITE_ID,
            is_public    = True,
            is_removed   = False,
            )

    def check_for_duplicate_comment(self, new):
        """
        Check that a submitted comment isn't a duplicate. This might be caused
        by someone posting a comment twice. If it is a dup, silently return the *previous* comment.
        """
        possible_duplicates = self.get_comment_model()._default_manager.using(
            self.target_object._state.db
        ).filter(
            content_type = new.content_type,
            object_pk = new.object_pk,
            user_name = new.user_name,
            user_email = new.user_email,
            user_url = new.user_url,
            )
        for old in possible_duplicates:
            if old.submit_date.date() == new.submit_date.date() and old.comment == new.comment:
                return old

        return new

    def clean_comment(self):
        """
        If COMMENTS_ALLOW_PROFANITIES is False, check that the comment doesn't
        contain anything in PROFANITIES_LIST.
        """
        comment = self.cleaned_data["comment"]
        if settings.COMMENTS_ALLOW_PROFANITIES == False:
            bad_words = [w for w in settings.PROFANITIES_LIST if w in comment.lower()]
            if bad_words:
                raise forms.ValidationError(ungettext(
                    "Watch your mouth! The word %s is not allowed here.",
                    "Watch your mouth! The words %s are not allowed here.",
                    len(bad_words)) % get_text_list(
                    ['"%s%s%s"' % (i[0], '-'*(len(i)-2), i[-1])
                     for i in bad_words], ugettext('and')))
        return comment

class CommentForm(CommentDetailsForm):
    honeypot      = forms.CharField(required=False,
                                    label=_('If you enter anything in this field ' \
                                            'your comment will be treated as spam'))

    def clean_honeypot(self):
        """Check that nothing's been entered into the honeypot."""
        value = self.cleaned_data["honeypot"]
        if value:
            raise forms.ValidationError(self.fields["honeypot"].label)
        return value


class MPTTCommentForm(CommentForm):
    parent = forms.ModelChoiceField(queryset=MPTTComment.objects.all(), required=False, widget=forms.HiddenInput)
    email_on_reply = forms.BooleanField(label=("Email me when someone replies to my comment thread"), required=False, initial=False, widget=forms.CheckboxInput)

    def __init__(self, *args, **kwargs):
        """
        Hide the 'URL' form field by default.
        """
        super(MPTTCommentForm, self).__init__(*args, **kwargs)
        self.fields['url'].widget = HiddenInput()
        self.fields['email'].widget = DEFAULT_EMAIL_WIDGET

    def get_comment_model(self):
        return MPTTComment

    def get_comment_create_data(self):
        data = super(MPTTCommentForm, self).get_comment_create_data()
        data['parent'] = self.cleaned_data['parent']
        data['email_on_reply'] = self.cleaned_data['email_on_reply']
        return data

    def clean(self):
        cleaned_data = super(MPTTCommentForm, self).clean()

        if 'email_on_reply' in cleaned_data and 'email' in cleaned_data:
            email_on_reply = cleaned_data.get('email_on_reply')
            email = cleaned_data.get('email')

            if email_on_reply and not email:
                self._errors['email'] = self.error_class([u"You must provide an email address to be notified of replies"])
                self._errors['email_on_reply'] = self.error_class([u"An email address is required"])
                del cleaned_data['email']
                del cleaned_data['email_on_reply']
        return cleaned_data


class EditCommentForm(forms.Form):

    ERROR_NO_PERMISSION = u"You do not have permission to edit this comment."
    comment = forms.CharField(max_length=COMMENT_MAX_LENGTH, label="Comment", widget=forms.Textarea)

    def __init__(self, request, comment, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial['comment'] = comment.comment
        kwargs['initial'] = initial
        super(EditCommentForm, self).__init__(*args, **kwargs)
        self.request = request
        self.comment = comment

    def clean(self):
        if not self.permission_to_edit():
            raise ValidationError(EditCommentForm.ERROR_NO_PERMISSION)
        return super(EditCommentForm, self).clean()

    def permission_to_edit(self):
        # by default only allow the comment author to edit the comment.  Subclasses can override
        return self.comment.user == self.request.user

    def save_changes(self):
        self.comment.comment = self.cleaned_data['comment']
        self.comment.full_clean()
        self.comment.save()

