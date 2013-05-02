from django.contrib.auth.decorators import login_required
from lazysignup.decorators import allow_lazy_user

@allow_lazy_user
def checkout(request):
    """
    Checkout a logged-in user.
    """
    pass


