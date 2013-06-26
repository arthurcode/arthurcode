from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, authenticate
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from arthurcode import settings
from django.contrib.sites.models import get_current_site
from django.http import HttpResponseRedirect
from accounts.forms import CustomerCreationForm, CustomerAuthenticationForm, CreatePublicProfileForm, ConvertLazyUserForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from lazysignup.decorators import is_lazy_user
from lazysignup.models import LazyUser
from decorators import non_lazy_login_required

@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_or_create_account(request,
          template_name='login_or_create_account.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.  Largely copied from the built-in auth login/ view.
    """
    redirect_to = _get_redirect_url(request, redirect_field_name)
    auth_form = None
    create_form = None

    if request.method == "POST":
        postdata = request.POST.copy()
        if u'login' in postdata:
            auth_form = CustomerAuthenticationForm(data=postdata)
            if auth_form.is_valid():
                # Okay, security check complete. Log the user in.
                auth_login(request, auth_form.get_user())

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                return HttpResponseRedirect(redirect_to)
        elif u'create' in postdata:
            create_form = _customer_creation_form(request, data=postdata)
            if create_form.is_valid():
                # Okay, security check complete. Create the new user and log them in.
                username = create_form.cleaned_data['username']
                password = create_form.cleaned_data['password2']
                if isinstance(create_form, ConvertLazyUserForm):
                    LazyUser.objects.convert(create_form)
                else:
                    create_form.save()
                user = authenticate(username=username, password=password)
                auth_login(request, user)

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()

                return HttpResponseRedirect(redirect_to)

    auth_form = auth_form or CustomerAuthenticationForm(request)
    create_form = create_form or _customer_creation_form(request)

    request.session.set_test_cookie()
    current_site = get_current_site(request)

    context = {
        'auth_form': auth_form,
        'create_form': create_form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
        }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, _template_name(redirect_to), context,
                            current_app=current_app)


def _customer_creation_form(request, *args, **kwargs):
    if is_lazy_user(request.user):
        return ConvertLazyUserForm(request.user, *args, **kwargs)
    return CustomerCreationForm(*args, **kwargs)


def _template_name(redirect_to):
    """
    tailor the look of the login page according to which url the user is being redirected to.  The redirect url will,
    for example, determine whether or not guest (lazy) users are allowed.
    """
    if redirect_to == reverse('checkout'):
        return 'login_checkout.html'
    if redirect_to.startswith('/questions/ask'):
        return 'login_ask_question.html'
    return 'login_no_guests.html'


def _get_redirect_url(request, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    If the user supplied redirection is either not present or unsafe the default LOGIN_REDIRECT_URL is returned.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')
    # Ensure the user-originating redirection url is safe.
    if not is_safe_url(url=redirect_to, host=request.get_host()):
        redirect_to = settings.LOGIN_REDIRECT_URL
    return redirect_to

@login_required
def create_public_profile(request):
    next = request.GET.get('next', None)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = CreatePublicProfileForm(request, data=post_data)
        if form.is_valid():
            form.create_profile()
            redirect_to = next or reverse('account_personal')
            return HttpResponseRedirect(redirect_to)
    else:
        form = CreatePublicProfileForm(request)

    context = {
        'form': form,
        'next': next
    }
    return render_to_response('create_public_profile.html', context, context_instance=RequestContext(request))


@non_lazy_login_required()
def view_orders(request):
    return render_to_response('orders.html', {}, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_personal(request):
    return render_to_response('personal.html', {}, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_wishlists(request):
    return render_to_response('wishlists.html', {}, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_reviews(request):
    return render_to_response('reviews.html', {}, context_instance=RequestContext(request))

