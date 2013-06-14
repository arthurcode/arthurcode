from django.contrib.auth.decorators import user_passes_test
from lazysignup.utils import is_lazy_user
from django.contrib.auth import REDIRECT_FIELD_NAME


def non_lazy_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and non-lazy, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated() and not is_lazy_user(u),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
