from utils.validators import not_blank


def validate_gc_number(number):
    """
    Throws an exception if the <number> is not a valid gift card number.
    """
    return not_blank(number)
