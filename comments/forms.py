__author__ = 'rhyanarthur'

from django import forms
from django.contrib.comments.forms import CommentForm
from django.forms.widgets import HiddenInput
from models import MPTTComment


class MPTTCommentForm(CommentForm):
    parent = forms.ModelChoiceField(queryset=MPTTComment.objects.all(), required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        """
        Hide the 'URL' form field by default.
        """
        super(MPTTCommentForm, self).__init__(*args, **kwargs)
        self.fields['url'].widget = HiddenInput()

        # add 'required' and 'aria-required' attributes to the widgets of required fields.  The fields will
        # render with these html attributes.  See http://john.foliot.ca/required-inputs/ for background on why
        # I'm adding these attributes.  TODO: determine if required='' is the same as required.
        for _, field in self.fields.iteritems():
            if field.required and field.widget:
                field.widget.attrs.update({'required': '',
                                           'aria-required': 'true'})

    def get_comment_model(self):
        return MPTTComment

    def get_comment_create_data(self):
        data = super(MPTTCommentForm, self).get_comment_create_data()
        data['parent'] = self.cleaned_data['parent']
        return data
