__author__ = 'rhyanarthur'

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


# utils
def is_blank(value):
    """
    Returns true if `value` is None, the empty string, or a string composed solely of whitespace.
    This method can handle both regular strings and unicode strings.
    """
    if not value:
        return True
    return isinstance(value, (str, unicode)) and not value.strip()