__author__ = 'rhyanarthur'

from django.core.exceptions import ValidationError
import re

ERROR_BLANK = "This field cannot be blank."  # same as built-in 'blank' error
ERROR_UPC = "The UPC must consist of exactly 12 digits."
ERROR_SKU = "The SKU must consist of 3-10 alphanumeric characters, cannot start with a 0, and may not contain the letters I, L or O."

UPC_PATTERN = re.compile('^\d{12}$')         # 12 digits
SKU_PATTERN = re.compile('^[1-9A-HJKMNP-Z][0-9A-HJKMNP-Z]{2,9}$')


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


def valid_sku(sku_str):
    """
    Tests that the given sku is valid:
      * must be between 3 and 10 alphanumeric characters in length (uppercase letters only)
      * cannot start with a 0
      * must not contain the letters (O, I, L) because they can be confused with numbers
      see http://www.clearlyinventory.com/inventory-basics/how-to-design-good-item-numbers-for-products-in-inventory
    """
    if not sku_str or not SKU_PATTERN.match(sku_str):
        raise ValidationError(ERROR_SKU)


# utils
def is_blank(value):
    """
    Returns true if `value` is None, the empty string, or a string composed solely of whitespace.
    This method can handle both regular strings and unicode strings.
    """
    if not value:
        return True
    return isinstance(value, (str, unicode)) and not value.strip()