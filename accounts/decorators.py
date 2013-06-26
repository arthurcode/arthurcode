from django.contrib.auth.decorators import user_passes_test
from lazysignup.utils import is_lazy_user
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse_lazy
from accountutils import is_regular_user


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


def public_profile_required(function=None):
    """
    Decorator for views that checks that the user has a public profile, redirecting to the create-public-profile
    page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.get_public_profile() is not None,
        login_url=reverse_lazy('create_public_profile'),
        redirect_field_name='next'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def public_profile_required_for_regular_users(function=None):
    actual_decorator = user_passes_test(
        lambda u: not is_regular_user(u) or u.get_public_profile() is not None,
        login_url=reverse_lazy('create_public_profile'),
        redirect_field_name='next'
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
