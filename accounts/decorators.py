from django.contrib.auth.decorators import user_passes_test
from lazysignup.utils import is_lazy_user
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.urlresolvers import reverse_lazy
from accountutils import is_regular_user, is_guest_passthrough
from functools import wraps
import urlparse


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


def lazy_users_choose_guest(func):
    """
    Requires that lazy users have explicitly chosen to access this view as a guest.
    """
    def wrapped(request, *args, **kwargs):
        if not is_lazy_user(request.user) or is_guest_passthrough(request):
            return func(request, *args, **kwargs)
        login_url = reverse_lazy('login_or_create_account')
        path = request.build_absolute_uri()
        # If the login url is the same scheme and net location then just
        # use the path as the "next" url.
        login_scheme, login_netloc = urlparse.urlparse(login_url)[:2]
        current_scheme, current_netloc = urlparse.urlparse(path)[:2]
        if ((not login_scheme or login_scheme == current_scheme) and
            (not login_netloc or login_netloc == current_netloc)):
            path = request.get_full_path()
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(path, login_url, 'next')
    return wraps(func)(wrapped)