from lazysignup.utils import is_lazy_user

GUEST_KEY = 'guest'


def is_regular_user(user):
    """
    Returns True if this is a user with an actual account.  Returns False for anonymous users and lazy users.
    """
    return user.is_authenticated() and not is_lazy_user(user)


def is_guest_passthrough(request):
    return request.GET.get(GUEST_KEY, False)
