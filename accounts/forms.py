from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
import hashlib
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from lazysignup.utils import is_lazy_user
from utils.validators import not_blank, is_blank
from accounts.models import PublicProfile, CustomerProfile, CustomerShippingAddress
from accounts.accountutils import is_regular_user
from django.contrib.auth.hashers import check_password
from django.db.transaction import commit_on_success
from utils.forms import CanadaShippingForm


SUBSCRIBE_TO_MAILING_LIST_LABEL = "Yes, email me information on current promotions and sales. (You can unsubscribe at any time)"

def username_from_email(email):
    md5 = hashlib.md5(email.lower())
    return md5.hexdigest()[:30]  # max 30 characters


class CustomerCreationForm(UserCreationForm):
    """
    A user creation form that requires an email instead of a username.  We attempt to generate a unique username
    from the email address using an md5 hash algorithm.
    """
    email = forms.EmailField(required=True)
    email2 = forms.EmailField(required=True, label="Email Confirmation",
                              help_text="Enter the same email as above, for verification.")
    on_mailing_list = forms.BooleanField(label=SUBSCRIBE_TO_MAILING_LIST_LABEL, initial=False)

    def __init__(self, *args, **kwargs):
        super(CustomerCreationForm, self).__init__(*args, **kwargs)
        # the username field won't be displayed on the form, it will be given a default (generated) value
        self.fields['username'].required = False
        # make sure the username is cleaned last, since it depends on email
        self.fields.keyOrder = ['email', 'email2', 'on_mailing_list', 'password1', 'password2', 'username']

    def clean_email2(self):
        email1 = self.cleaned_data.get('email', None)
        email2 = self.cleaned_data.get('email2', None)

        if email1 and email2 and not email1 == email2:
            raise ValidationError("The two email fields did not match")
        return email2

    def clean_username(self):
        """
        Set the username to be the first 30 (of 32) characters of the md5 hash of the lower-case email address.
        Collisions are possible, but should be rare (I hope).
        """
        email = self.cleaned_data.get('email', None)
        if email:
            self.cleaned_data['username'] = username_from_email(email)
            try:
                return super(CustomerCreationForm, self).clean_username()
            except ValidationError, e:
                if unicode(self.error_messages['duplicate_username']) in unicode(e):
                    # the generated username is not unique
                    same_email_count = User.objects.filter(email=email).count()
                    if same_email_count > 0:
                        self.errors['email'] = self.error_class([u'A user with this email address already exists.'])
                    else:
                        # hmmm, this must be a hash algorithm collision
                        self.errors['email'] = self.error_class([u'Sorry, we were unable to generate a unique username from '
                                                                u'this email address. You will need to register with'
                                                                u' a different email address.'])
                raise e
        else:
            return super(CustomerCreationForm, self).clean_username()

    def save(self, commit=True):
        """
        Be aware that the 'on_mailing_list' field is only saved to the public-profile when commit=True.  Code that
        calls commit=False will have to handle that field manually.
        """
        user = super(CustomerCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.get_customer_profile() or CustomerProfile(user=user)
            profile.on_mailing_list = self.cleaned_data['on_mailing_list']
            profile.full_clean()
            profile.save()
        return user


class ConvertLazyUserForm(CustomerCreationForm):

    def __init__(self, lazyUser, *args, **kwargs):
        email = lazyUser.email
        initial = kwargs.get('initial', {})

        if not is_blank(email):
            initial['email'] = email
            if 'data' in kwargs:
                kwargs['data']['email'] = email
                kwargs['data']['email2'] = email

        customer_profile = lazyUser.get_customer_profile()
        if customer_profile and customer_profile.on_mailing_list:
            # don't make it easier than necessary for them to un-subscribe from the mailing list
            initial['on_mailing_list'] = True

        kwargs['initial'] = initial

        super(ConvertLazyUserForm, self).__init__(*args, **kwargs)
        self.instance = lazyUser


class CustomerAuthenticationForm(AuthenticationForm):

    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(CustomerAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields.keyOrder = ['email', 'password', 'username']
        self.error_messages['invalid_login'] = u'Incorrect email/password combination. Note that both fields are case sensitive.'

    def clean_username(self):
        email = self.cleaned_data.get('email', '')
        if email:
            return username_from_email(email)
        return ''


class CreatePublicProfileForm(forms.Form):
    username = forms.CharField(max_length=PublicProfile.NAME_LENGTH, validators=[not_blank],
                               help_text="will be displayed publicly on your reviews and comments.")
    description = forms.CharField(max_length=PublicProfile.DESCRIPTION_LENGTH, required=False,
                                  help_text="describe yourself in %d characters or less.  "
                                            "Example: 'artist and mother of 2'" % PublicProfile.DESCRIPTION_LENGTH)
    location = forms.CharField(max_length=PublicProfile.LOCATION_LENGTH, required=False,
                               help_text="Examples: 'Edmonton, AB', 'Saskatchewan'")

    def __init__(self, request, *args, **kwargs):
        super(CreatePublicProfileForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        data = super(CreatePublicProfileForm, self).clean()
        if not self.request.user.is_authenticated():
            raise ValidationError(u"You must be logged-in to create a public profile.")
        return data

    def create_profile(self, commit=True):
        profile = PublicProfile(user=self.request.user)
        profile.username = self.cleaned_data['username']
        profile.description = self.cleaned_data['description']
        profile.location = self.cleaned_data['location']

        if commit:
            profile.full_clean()
            profile.save()
        return profile


class EditPublicProfileForm(CreatePublicProfileForm):

    def __init__(self, request, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial.update(self.make_initial_dict(request))
        kwargs['initial'] = initial
        super(EditPublicProfileForm, self).__init__(request, *args, **kwargs)

    def make_initial_dict(self, request):
        profile = request.user.get_public_profile()
        if not profile:
            return {}
        return {
            'username': profile.username,
            'description': profile.description,
            'location': profile.location,
        }

    def save(self, commit=True):
        profile = self.request.user.get_public_profile()
        if not profile:
            return self.create_profile(commit=commit)
        profile.username = self.cleaned_data['username']
        profile.description = self.cleaned_data['description']
        profile.location = self.cleaned_data['location']
        if commit:
            profile.full_clean()
            profile.save()
        return profile


class ChangeEmailForm(forms.Form):
    """
    Gives registered users a way to change their email address.  Their account password is required for security
    reasons.
    """

    new_email = forms.EmailField(label="New Email Address")
    password = forms.CharField(widget=forms.PasswordInput,
                               help_text="For security reasons please enter your account password.")

    def __init__(self, request, *args, **kwargs):
        super(ChangeEmailForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean_new_email(self):
        email = self.cleaned_data.get('new_email', None)
        if email and email == self.request.user.email:
            raise ValidationError("This email address is the same as the one that is already on file.")
        return email

    def clean_password(self):
        password = self.cleaned_data.get('password', None)
        if password and not check_password(password, self.request.user.password):
            raise ValidationError("Incorrect password")

    def clean(self):
        data = super(ChangeEmailForm, self).clean()
        if not is_regular_user(self.request.user):
            raise ValidationError("This form can only be used by registered users.")

        new_email = self.cleaned_data.get('new_email', None)
        if new_email:
            username = username_from_email(new_email)
            if User.objects.filter(username=username).exists():
                 # the generated username is not unique
                if User.objects.filter(email=new_email).exists():
                    self.errors['new_email'] = self.error_class([u'A user with this email address already exists.'])
                else:
                    # hmmm, this must be a hash algorithm collision
                    self.errors['new_email'] = self.error_class([u'Sorry, we were unable to generate a unique username from '
                                                                u'this email address. You will need to register with'
                                                                u' a different email address.'])
        return data

    @commit_on_success
    def do_change_email(self):
        # since the username is derived from the email they both have to change at the same time
        email = self.cleaned_data.get('new_email')
        username = username_from_email(email)
        self.request.user.username = username
        self.request.user.email = email
        self.request.user.save()


class ContactInfoForm(forms.Form):

    # similar to CustomerProfile contact method choices, minus the 'unknown' choice
    CONTACT_METHOD_CHOICES = ((CustomerProfile.EMAIL, 'Email'),
                              (CustomerProfile.PHONE, 'Phone'))

    ERROR_PHONE_REQUIRED = u"A phone number is required because you selected 'Phone' as your preferred contact method."

    first_name = forms.CharField(max_length=30, required=True)  # 30 is the max length set by User
    last_name = forms.CharField(max_length=30, required=True)   # 30 is the max length set by User
    email = forms.EmailField(required=True)
    email2 = forms.EmailField(required=True, label="Retype Email")
    contact_method = forms.ChoiceField(choices=CONTACT_METHOD_CHOICES, initial=CustomerProfile.EMAIL,
                                       widget=forms.RadioSelect,
                                       label="If there is a problem with your order how should we contact you?")
    phone = forms.CharField(max_length=20, required=False)
    on_mailing_list = forms.BooleanField(label=SUBSCRIBE_TO_MAILING_LIST_LABEL, initial=False, required=False)

    def __init__(self, request, *args, **kwargs):
        if 'data' in kwargs and kwargs['data']:
            if request.user.is_authenticated and not is_lazy_user(request.user) and request.user.email:
                # it's not a simple thing to change a register's user's email address, don't let them do that from
                # this form
                kwargs['data']['email'] = request.user.email
                kwargs['data']['email2'] = request.user.email

        super(ContactInfoForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean_email2(self):
        email1 = self.cleaned_data.get('email', None)
        email2 = self.cleaned_data.get('email2', '')
        if email1 and email2 and email1 != email2:
            raise ValidationError(u"The two email addresses do not match.")
        return email2

    def clean(self):
        cleaned_data = super(ContactInfoForm, self).clean()
        contact_method = cleaned_data.get('contact_method', None)
        phone = cleaned_data.get('phone', None)

        if contact_method and int(contact_method) == CustomerProfile.PHONE and not phone:
            # a phone number wasn't entered, indicate that it is now conditionally required.
            self._errors['contact_method'] = self.error_class([ContactInfoForm.ERROR_PHONE_REQUIRED])
            self._errors['phone'] = self.error_class([ContactInfoForm.ERROR_PHONE_REQUIRED])
            del(cleaned_data['contact_method'])

        return cleaned_data


class EditContactInfo(ContactInfoForm):

    def __init__(self, request, *args, **kwargs):
        initial = kwargs.get('initial', {})
        initial.update(self.make_initial_dict(request))
        kwargs['initial'] = initial
        super(EditContactInfo, self).__init__(request, *args, **kwargs)
        self.request = request

    def make_initial_dict(self, request):
        user = request.user
        if not user.is_authenticated:
            return {}

        initial = {
            'email': user.email,
            'email2': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }

        profile = user.get_customer_profile()
        if profile:
            initial.update({
                'contact_method': profile.contact_method,
                'phone': profile.phone,
                'on_mailing_list': profile.on_mailing_list
            })
        return initial

    def save(self):
        # save the edited contact information back to this user's account table
        # never change a registered user's email address using this form
        user = self.request.user
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        new_email = self.cleaned_data.get('email')

        if not user.email or not is_regular_user(user):
            user.email = new_email

        profile = user.get_customer_profile()
        if not profile:
            profile = CustomerProfile(user=user)

        profile.phone = self.cleaned_data.get('phone')
        profile.contact_method = self.cleaned_data.get('contact_method')
        profile.on_mailing_list = self.cleaned_data.get('on_mailing_list')

        profile.full_clean()
        profile.save()
        user.full_clean()
        user.save()
        return user


class CustomerShippingAddressForm(CanadaShippingForm):
    """
    A shipping address form that includes a 'nickname' field.  The nickname will be used by the customer to easily
    distinguish an address from others in his/her address book.
    """

    nickname = forms.CharField(max_length=CustomerShippingAddress.NICKNAME_MAX_LENGTH, label="Nickname",
                            help_text="Something to distinguish this address from the others in your address book. " +
                                      "Examples: 'Aunt Mary', 'Flower Shop'", validators=[not_blank])

    def __init__(self, customer, *args, **kwargs):
        super(CustomerShippingAddressForm, self).__init__(*args, **kwargs)
        self.customer = customer

    def clean(self):
        data = super(CustomerShippingAddressForm, self).clean()
        nickname = self.cleaned_data.get('nickname', None)
        address_id = self.cleaned_data.get('address_id', None)
        if nickname and self.customer:
            if CustomerShippingAddress.objects.filter(nickname=nickname, customer=self.customer).exclude(id=address_id).exists():
                self._errors['nickname'] = self.error_class([u"An address with this nickname already exists."])
                del(data['nickname'])
        return data

    def save(self, clazz, commit=True):
        address = super(CustomerShippingAddressForm, self).save(clazz, commit=False)
        address.nickname = self.cleaned_data.get('nickname')
        address.customer = self.customer
        if commit:
            address.save()
        return address



