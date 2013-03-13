__author__ = 'rhyanarthur'

from django import forms
from django.contrib.comments.forms import CommentForm
from django.forms.widgets import HiddenInput
from models import MPTTComment
from django.utils.html import escape

# http://www.thebitguru.com/blog/view/299-Adding%20*%20to%20required%20fields

REQUIRED_TEXT = "(required)"


def add_required_label_tag(original_function):
    """
    A function intended to decorate BoundField.label_tag().  The labels of required fields are automatically
    given a 'required' html class, and '(required)' is appended to the label text.
    """
    def required_label_tag(self, contents=None, attrs=None):
        contents = contents or escape(self.label)

        if self.field.required:
            # add the required class to the label's html
            attrs = _add_class_attr(attrs, 'required')

            # add text to the label to make it clear that the field is required.
            required_label = "<span class='required-text'>%s</span>" % REQUIRED_TEXT

            if required_label not in contents:
                contents += " %s" % required_label

        return original_function(self, contents, attrs)
    return required_label_tag


def add_field_errors_to_label(original_function):
    """
    A function intended to decorate BoundField.label_tag().  If the field has errors they will be printed inside the
    field's label tag.  The label is the best place to put these errors for accessibility reasons.  When errors are
    present the label will be rendered with the 'error' html class.
    """
    def field_errors_label_tag(self, contents=None, attrs=None):
        contents = contents or escape(self.label)
        if self._errors():
            contents += " <span class='error'>%s</span>" % self._errors().as_text()
            attrs = _add_class_attr(attrs, 'error')
        return original_function(self, contents, attrs)
    return field_errors_label_tag


def _add_class_attr(attrs, clazz):
    attrs = attrs or {}
    if 'class' in attrs:
        existing_classes = attrs['class'].split()
        if clazz not in existing_classes:
            existing_classes.append(clazz)
            attrs['class'] = ' '.join(existing_classes)
    else:
        attrs.update({'class': clazz})
    return attrs


def decorate_bound_field():
    from django.forms.forms import BoundField
    BoundField.label_tag = add_field_errors_to_label(BoundField.label_tag)
    BoundField.label_tag = add_required_label_tag(BoundField.label_tag)

decorate_bound_field()


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
