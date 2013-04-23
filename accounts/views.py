from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from arthurcode import settings
from django.contrib.sites.models import get_current_site
from django.http import HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_or_create_account(request,
          template_name='login_or_create_account.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.  Largely copied from the built-in auth login/ view.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    auth_form = None

    if request.method == "POST":
        postdata = request.POST.copy()
        if u'login' in postdata:
            auth_form = authentication_form(data=postdata)
            if auth_form.is_valid():
                # Ensure the user-originating redirection url is safe.
                if not is_safe_url(url=redirect_to, host=request.get_host()):
                    redirect_to = settings.LOGIN_REDIRECT_URL

                # Okay, security check complete. Log the user in.
                auth_login(request, auth_form.get_user())

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                return HttpResponseRedirect(redirect_to)

    auth_form = auth_form or authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'auth_form': auth_form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
                            current_app=current_app)

@login_required()
def show_account(request):
    """
    Shows a user's account settings.  In this context the user is a customer
    """
    return render_to_response('my_account.html', locals(), context_instance=RequestContext(request))
