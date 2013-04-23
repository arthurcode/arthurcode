from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


def choose_checkout_method(request):
    """
    The user can choose to checkout with google checkout, checkout using our server as a guest, or log in / create an
    account and then check out.
    """
    if request.user.is_authenticated():
        # since they are logged in already, we just check them out as a customer.  I'll have to revisit this if and
        # when I incorporate alternative checkout gateways (such as google checkout)
        return HttpResponseRedirect(reverse('account_checkout'))

    # display a standard login or create account form, but with a giant 'checkout-as-guest' escape link
    pass


def checkout_as_guest(request):
    """
    Run the current user through the checkout process as a guest.
    Check that the user isn't actually logged in - if they are, redirect them to the checkout
    for logged-in users.
    """
    pass


@login_required()
def checkout_account(request):
    """
    Checkout a logged-in user.
    """
    pass