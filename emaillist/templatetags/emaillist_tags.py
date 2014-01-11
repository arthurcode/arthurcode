from django.template import Library
from emaillist.utils import is_on_list
register = Library()

@register.filter
def on_mailing_list(user):
    """
    Returns true iff the given user's email address has been added to our mailing list.
    """
    return user and user.email and is_on_list(user.email)
