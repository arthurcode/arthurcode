from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


def checkout_as_guest(request):
    """
    Run the current user through the checkout process as a guest.
    Check that the user isn't actually logged in - if they are, redirect them to the checkout
    for logged-in users.
    """
    pass


@login_required()
def checkout(request):
    """
    Checkout a logged-in user.
    """
    pass