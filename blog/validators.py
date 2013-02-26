__author__ = 'rhyanarthur'

from blog.utils import is_blank
from django.core.exceptions import ValidationError

ERROR_BLANK = "This field cannot be blank."  # same as built-in 'blank' error


def not_blank(value):
    """
    Tests for blank values.  The difference between the built-in 'blank' validation and this method is that this
    method will disallow strings containing only whitespace.  By default Django doesn't consider these types of string
    to be 'blank'.
    """
    if is_blank(value):
        raise ValidationError(ERROR_BLANK)