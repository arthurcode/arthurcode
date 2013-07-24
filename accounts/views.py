from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, authenticate
from django.template.response import TemplateResponse
from django.utils.http import is_safe_url
from arthurcode import settings
from django.contrib.sites.models import get_current_site
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from accounts.forms import CustomerCreationForm, CustomerAuthenticationForm, CreatePublicProfileForm, \
    ConvertLazyUserForm, ChangeEmailForm, EditContactInfo, EditPublicProfileForm, CustomerShippingAddressForm, \
    CustomerBillingAddressForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from lazysignup.decorators import is_lazy_user
from lazysignup.models import LazyUser
from decorators import non_lazy_login_required
from orders.models import Order
from django.contrib.auth.views import password_change, password_change_done, logout as auth_logout, \
    password_reset, password_reset_done, password_reset_confirm, password_reset_complete
from accounts.models import CustomerShippingAddress, CustomerProfile, CustomerBillingAddress

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
            redirect_to = next or reverse('account_personal') + "#public"
            return HttpResponseRedirect(redirect_to)
    else:
        profile = request.user.get_public_profile()
        if profile:
            # this user already has a public profile
            return HttpResponseRedirect(reverse('edit_public_profile'))
        form = CreatePublicProfileForm(request)

    context = {
        'form': form,
        'next': next
    }
    return render_to_response('create_public_profile.html', context, context_instance=RequestContext(request))


@login_required
def edit_public_profile(request):
    next = request.GET.get('next', None)

    if request.method == "POST":
        post_data = request.POST.copy()
        form = EditPublicProfileForm(request, data=post_data)
        if form.is_valid():
            form.save(commit=True)
            redirect_to = next or reverse('account_personal') + "#public"
            return HttpResponseRedirect(redirect_to)
    else:
        form = EditPublicProfileForm(request)

    context = {
        'form': form,
        'next': next,
    }
    return render_to_response('edit_public_profile.html', context, context_instance=RequestContext(request))


@non_lazy_login_required()
def view_orders(request):
    orders = Order.objects.filter(customer__user=request.user).order_by('-date')
    context = {
        'orders': orders,
    }
    return render_to_response('orders.html', context, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_personal(request):
    public_profile = request.user.get_public_profile()
    customer_profile = request.user.get_customer_profile()
    context = {
        'public_profile': public_profile,
        'customer_profile': customer_profile
    }
    return render_to_response('personal.html', context, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_wishlists(request):
    return render_to_response('wishlists.html', {}, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_reviews(request):
    return render_to_response('reviews.html', {}, context_instance=RequestContext(request))

@non_lazy_login_required()
@sensitive_post_parameters()
@never_cache
def change_email(request):
    next = request.GET.get('next', None)
    if request.method == "POST":
        post_data = request.POST.copy()
        form = ChangeEmailForm(request, data=post_data)
        if form.is_valid():
            redirect_to = next or reverse('account_personal')
            form.do_change_email()
            return HttpResponseRedirect(redirect_to)
    else:
        form = ChangeEmailForm(request)
    context = {
        'form': form,
        'next': next
    }
    return render_to_response('registration/change_email.html', context, context_instance=RequestContext(request))


@non_lazy_login_required()
@sensitive_post_parameters()
@never_cache
def change_password(request):
    next = request.GET.get('next', None) or reverse('account_change_password_done')
    template = 'registration/change_password.html'
    return password_change(request, template_name=template, post_change_redirect=next)


@require_GET
def change_password_done(request):
    return password_change_done(request, template_name='registration/change_password_done.html')


@non_lazy_login_required()
def logout(request):
    return auth_logout(request, template_name='registration/after_log_out.html', redirect_field_name='next')


def reset_password(request):
    template_name = 'registration/reset_my_password.html'
    email_template_name = 'registration/reset_my_password_email.html'
    subject_template_name = 'registration/reset_my_password_subject.txt'
    post_reset_redirect = reverse('account_reset_password_done')
    return password_reset(request, is_admin_site=False, template_name=template_name,
                            email_template_name=email_template_name, subject_template_name=subject_template_name,
                            post_reset_redirect=post_reset_redirect)


@require_GET
def reset_password_done(request):
    template_name = 'registration/reset_my_password_done.html'
    return password_reset_done(request, template_name=template_name)


def reset_password_confirm(request, uidb36=None, token=None):
    redirect_to = reverse('account_reset_password_complete')
    template_name = 'registration/reset_my_password_confirm.html'
    return password_reset_confirm(request, uidb36=uidb36, token=token, post_reset_redirect=redirect_to,
                                  template_name=template_name)


def reset_password_complete(request):
    template = 'registration/reset_my_password_complete.html'
    return password_reset_complete(request, template_name=template)


def edit_contact_info(request):
    if request.method == "POST":
        post_data = request.POST.copy()
        form = EditContactInfo(request, data=post_data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('account_personal') + "#contact")
    else:
        form = EditContactInfo(request)

    context = {
        'form': form,
    }
    return render_to_response('edit_contact_info.html', context, context_instance=RequestContext(request))


@non_lazy_login_required()
def add_shipping_address(request):
    """
    Adds a new shipping address to this customer's profile
    """
    template_name = 'add_shipping_address.html'
    redirect_to = reverse('account_personal') + '#shipping'
    form_clazz = CustomerShippingAddressForm
    model_clazz = CustomerShippingAddress
    return _add_address(request, template_name, redirect_to, form_clazz, model_clazz)


@non_lazy_login_required()
def add_billing_address(request):
    """
    Adds a new billing address to this customer's profile
    """
    template_name = 'add_billing_address.html'
    redirect_to = reverse('account_personal') + '#billing'
    form_clazz = CustomerBillingAddressForm
    model_clazz = CustomerBillingAddress
    return _add_address(request, template_name, redirect_to, form_clazz, model_clazz)


def _add_address(request, template_name, redirect_to, form_clazz, model_clazz):
    profile = request.user.get_customer_profile()
    save_profile = False
    if not profile:
        profile = CustomerProfile(user=request.user)
        save_profile = True

    if request.method == "POST":
        post_data = request.POST.copy()
        form = form_clazz(profile, data=post_data)
        if form.is_valid():
            if save_profile:
                profile.full_clean()
                profile.save()
            form.save(model_clazz, commit=True)
            return HttpResponseRedirect(redirect_to)
    else:
        form = form_clazz(profile)
    context = {
        'form': form,
    }
    return render_to_response(template_name, context, context_instance=RequestContext(request))


@non_lazy_login_required()
@require_POST
def delete_shipping_address(request, address_id, redirect_to=None):
    return _delete_address(request, address_id, CustomerShippingAddress, redirect_to)


@non_lazy_login_required()
@require_POST
def delete_billing_address(request, address_id, redirect_to=None):
    return _delete_address(request, address_id, CustomerBillingAddress, redirect_to)


def _delete_address(request, address_id, model_clazz, redirect_to):
    """
    Addresses can only be deleted by the user that 'owns' them.  Staff members can delete addresses through the admin
    interface if need be.
    """
    address = get_object_or_404(model_clazz, id=address_id)
    if not address.customer.user == request.user:
        return HttpResponseForbidden(u"You do not have permission to delete this address.")
    redirect_to = redirect_to or request.GET.get('next', None)

    if not redirect_to:
        if model_clazz == CustomerShippingAddress:
            redirect_to = reverse('account_personal') + '#shipping'
        else:
            redirect_to = reverse('account_personal') + '#billing'

    address.delete()
    return HttpResponseRedirect(redirect_to)



