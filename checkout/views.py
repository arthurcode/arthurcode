from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from checkout.forms import ContactInfoForm
from django.template import RequestContext

@login_required()
def checkout(request):
    """
    Checkout a logged-in user.
    """
    pass


