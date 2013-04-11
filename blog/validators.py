__author__ = 'rhyanarthur'

from blog.utils import is_blank
from django.core.exceptions import ValidationError
import re

ERROR_BLANK = "This field cannot be blank."  # same as built-in 'blank' error
ERROR_UPC = "The UPC must consist of exactly 12 digits."

UPC_PATTERN = re.compile('^\d{12}$')         # 12 digits


def not_blank(value):
    """
    Tests for blank values.  The difference between the built-in 'blank' validation and this method is that this
    method will disallow strings containing only whitespace.  By default Django doesn't consider these types of string
    to be 'blank'.
    """
    if is_blank(value):
        raise ValidationError(ERROR_BLANK)


def valid_upc(upc_str):
    """
    Tests that the upc string is composed of exactly 12 digits.
    """
    if not upc_str or not UPC_PATTERN.match(upc_str):
        raise ValidationError(ERROR_UPC)