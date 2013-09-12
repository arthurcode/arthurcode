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
from utils.storeutils import get_products_needing_review
from reviews.models import Review

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
    if request.method == "POST":
        postdata = request.POST.copy()
        auth_form = CustomerAuthenticationForm(data=postdata)
        if auth_form.is_valid():
            # Okay, security check complete. Log the user in.
            auth_login(request, auth_form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            return HttpResponseRedirect(redirect_to)
    else:
        auth_form = CustomerAuthenticationForm(request)

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
    return TemplateResponse(request, _template_name(redirect_to), context,
                            current_app=current_app)


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


@sensitive_post_parameters()
@csrf_protect
@never_cache
def create_account(request):
    next = request.GET.get('next', None)
    if request.method == "POST":
        postdata = request.POST.copy()
        create_form = CustomerCreationForm(data=postdata)
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

            redirect_to = _get_redirect_url(request, 'next')
            return HttpResponseRedirect(redirect_to)
    else:
        create_form = CustomerCreationForm()

    request.session.set_test_cookie()

    context = {
        'create_form': create_form,
        'next': next,
    }
    return render_to_response('create_account.html', context, context_instance=RequestContext(request))


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
    orders = Order.objects.filter(user=request.user).order_by('-date')
    context = {
        'orders': orders,
    }
    return render_to_response('orders.html', context, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_personal(request):
    public_profile = request.user.get_public_profile()
    customer_profile = request.user.get_customer_profile()
    shipping_addresses = None
    billing_address = None

    if customer_profile:
        shipping_addresses = customer_profile.shipping_addresses.order_by('nickname')
        try:
            billing_address = customer_profile.billing_address
        except CustomerBillingAddress.DoesNotExist:
            pass

    context = {
        'public_profile': public_profile,
        'customer_profile': customer_profile,
        'shipping_addresses': shipping_addresses,
        'billing_address': billing_address,
    }
    return render_to_response('personal.html', context, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_wishlists(request):
    return render_to_response('wishlists.html', {}, context_instance=RequestContext(request))

@non_lazy_login_required()
def view_reviews(request):
    reviews = Review.objects.filter(user=request.user)
    needing_review = get_products_needing_review(request)
    context = {
        'reviews': reviews,
        'needing_review': needing_review,
    }
    return render_to_response('reviews.html', context, context_instance=RequestContext(request))

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
    profile = request.user.get_customer_profile()
    initial_data = {}

    if profile and profile.shipping_addresses.count() == 0:
        initial_data['nickname'] = 'Me'  # encourage users to first add a 'Me' address.  They can change it if they want.

    return _add_address(request, template_name, redirect_to, form_clazz, model_clazz, initial_data)


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


def _add_address(request, template_name, redirect_to, form_clazz, model_clazz, initial_data=None):
    profile = request.user.get_customer_profile()
    save_profile = False
    if not profile:
        profile = CustomerProfile(user=request.user)
        save_profile = True

    if request.method == "POST":
        post_data = request.POST.copy()
        form = form_clazz(customer=profile, data=post_data)
        if form.is_valid():
            if save_profile:
                profile.full_clean()
                profile.save()
            form.save(model_clazz, commit=True)
            return HttpResponseRedirect(redirect_to)
    else:
        form = form_clazz(customer=profile, initial=initial_data)
    context = {
        'form': form,
    }
    return render_to_response(template_name, context, context_instance=RequestContext(request))


@non_lazy_login_required()
def edit_shipping_address(request, address_id):
    redirect_to = request.GET.get('next', None) or reverse('account_personal') + '#shipping'
    template_name = "edit_shipping_address.html"
    model_clazz = CustomerShippingAddress
    form_clazz = CustomerShippingAddressForm
    return _edit_address(request, address_id, model_clazz, form_clazz, redirect_to, template_name)


@non_lazy_login_required()
def edit_billing_address(request, address_id):
    redirect_to = request.GET.get('next', None) or reverse('account_personal') + '#billing'
    template_name = "edit_billing_address.html"
    model_clazz = CustomerBillingAddress
    form_clazz = CustomerBillingAddressForm
    return _edit_address(request, address_id, model_clazz, form_clazz, redirect_to, template_name)


def _edit_address(request, address_id, address_clazz, form_clazz, redirect_to, template_name):
        profile = request.user.get_customer_profile()
        address = get_object_or_404(address_clazz, id=address_id)

        if not address.customer.user == request.user:
            return HttpResponseForbidden(u"You are not permitted to edit another customer's address")

        if request.method == "POST":
            data = request.POST.copy()
            data['address_id'] = address_id
            form = form_clazz(customer=profile, address_id=address_id, data=data)
            if form.is_valid():
                form.save(address_clazz, commit=True)
                return HttpResponseRedirect(redirect_to)
        else:
            form = form_clazz(customer=profile, address_id=address_id, initial=address.as_dict())

        context = {
            'form': form,
        }
        return render_to_response(template_name, context, context_instance=RequestContext(request))


@non_lazy_login_required()
def delete_shipping_address(request, address_id, redirect_to=None):
    redirect_to = redirect_to or request.GET.get('next', None) or reverse('account_personal') + '#shipping'
    template_name = 'delete_shipping_address.html'
    return _delete_address(request, address_id, CustomerShippingAddress, redirect_to, template_name)


@non_lazy_login_required()
def delete_billing_address(request, address_id, redirect_to=None):
    redirect_to = redirect_to or request.GET.get('next', None) or reverse('account_personal') + '#billing'
    template_name = 'delete_billing_address.html'
    return _delete_address(request, address_id, CustomerBillingAddress, redirect_to, template_name)


def _delete_address(request, address_id, model_clazz, redirect_to, template_name):
    """
    Addresses can only be deleted by the user that 'owns' them.  Staff members can delete addresses through the admin
    interface if need be.
    """
    address = get_object_or_404(model_clazz, id=address_id)
    if not address.customer.user == request.user:
        return HttpResponseForbidden(u"You do not have permission to delete this address.")

    if request.method == "POST":
        if "yes" in request.POST:
            address.delete()
        return HttpResponseRedirect(redirect_to)
    context = {
        'address': address,
    }
    return render_to_response(template_name, context, context_instance=RequestContext(request))



