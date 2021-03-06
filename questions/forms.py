from django import forms
from comments.forms import MPTTCommentForm, EditCommentForm
from accounts.accountutils import is_regular_user
from django.core.exceptions import ValidationError


class AskQuestionForm(MPTTCommentForm):

    def __init__(self, request, product, *args, **kwargs):
        self.request = request
        # under certain conditions pre-fil the data dict with the user's saved email address
        if not self.ask_for_email():
            if 'data' in kwargs:
                kwargs['data']['email'] = self.request.user.email

        super(AskQuestionForm, self).__init__(product, *args, **kwargs)
        # the 'parent' field needs to remain null because a question is always top-level.
        # email-on-reply is always going to be true because what is the point of asking a question if you don't want
        # to hear the answer.
        self.fields['email'].required = True
        email_on_reply = self.fields['email_on_reply']
        email_on_reply.initial = True
        email_on_reply.widget = forms.HiddenInput()

        self.fields['comment'].label = "Question"

        # Don't require a name.  If the user has an associated public profile use that name, otherwise we'll just tag
        # the question as 'anonymous'
        name = self.fields['name']
        name.required = False
        name.widget = forms.HiddenInput()

    def ask_for_email(self):
        return not is_regular_user(self.request.user) or not self.request.user.email

    def get_comment_create_data(self):
        data = super(AskQuestionForm, self).get_comment_create_data()
        if self.request.user.is_authenticated():
            data['user'] = self.request.user
        data['ip_address'] = self.request.META.get("REMOTE_ADDR", None)
        return data


class EditQuestionForm(EditCommentForm):

    def __init__(self, *args, **kwargs):
        super(EditQuestionForm, self).__init__(*args, **kwargs)
        self.fields['comment'].label = "Question"


class AnswerQuestionForm(MPTTCommentForm):
    """
    At the moment questions can only be answered by staff members.
    """

    def __init__(self, request, question, *args, **kwargs):
        if 'data' in kwargs:
            # link the answer to the question
            kwargs['data']['parent'] = question.id

        super(AnswerQuestionForm, self).__init__(question.content_object, *args, **kwargs)
        self.request = request
        self.question = question
        self.fields['name'].required = False
        self.fields['comment'].label = "Answer"

    def clean(self):
        data = super(AnswerQuestionForm, self).clean()
        if not self.request.user.is_staff:
            raise ValidationError(u"Sorry, only staff members are allowed to answer customer questions.")
        return data

    def get_comment_create_data(self):
        data = super(AnswerQuestionForm, self).get_comment_create_data()
        data['user'] = self.request.user
        data['ip_address'] = self.request.META.get("REMOTE_ADDR", None)
        return data

