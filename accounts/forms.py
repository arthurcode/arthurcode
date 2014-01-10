from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
import hashlib
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from utils.validators import not_blank
from accounts.models import PublicProfile, CustomerProfile, CustomerShippingAddress
from accounts.accountutils import is_regular_user
from django.contrib.auth.hashers import check_password
from django.db.transaction import commit_on_success
from utils.forms import CanadaShippingForm, BillingForm
from django.core.urlresolvers import reverse
from emaillist.models import EmailListItem
import logging

logger = logging.getLogger(__name__)

SUBSCRIBE_TO_MAILING_LIST_LABEL = "Yes, email me information on current promotions and sales."
SUBSCRIBE_TO_MAILING_LIST_HELP = "If you subscribe to our mailing list, you will receive promotional email from us <em>at most</em> once every two weeks.<br> <em>You can unsubscribe at any time.</em>"

def get_readonly_email_help():
  return u"For security reasons your email address cannot be modified from this form. <a href='%s'>Click here to edit it.</a>" % reverse('account_change_email')

EMAIL_INPUT_SIZE = 30        # visible size
EMAIL_MAXLENGTH = 75   # actual character maximum

FIRST_NAME_INPUT_SIZE = 30
FIRST_NAME_MAXLENGTH = 30

LAST_NAME_INPUT_SIZE = 30
LAST_NAME_MAXLENGTH = 30

PHONE_INPUT_SIZE = 12
PHONE_MAXLENGTH = 20

DEFAULT_EMAIL_WIDGET = forms.TextInput(attrs={'size': EMAIL_INPUT_SIZE, 'maxlength': EMAIL_MAXLENGTH})
DEFAULT_NAME_WIDGET = forms.TextInput(attrs={'size': FIRST_NAME_INPUT_SIZE, 'maxlength': FIRST_NAME_MAXLENGTH})
DEFAULT_PHONE_WIDGET = forms.TextInput(attrs={'size': PHONE_INPUT_SIZE, 'maxlength': PHONE_MAXLENGTH})
DEFAULT_PASSWORD_WIDGET = forms.PasswordInput(attrs={'size': 30, 'maxlength': 125})
DEFAULT_NICKNAME_WIDGET = forms.TextInput(attrs={'size': 30, 'maxlength': CustomerShippingAddress.NICKNAME_MAX_LENGTH})
DEFAULT_PROFILE_USERNAME_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength': PublicProfile.NAME_LENGTH})


def username_from_email(email):
    md5 = hashlib.md5(email.lower())
    return md5.hexdigest()[:30]  # max 30 characters


class CustomerCreationForm(UserCreationForm):
    """
    A user creation form that requires an email instead of a username.  We attempt to generate a unique username
    from the email address using an md5 hash algorithm.
    """
    email = forms.EmailField(required=True, widget=DEFAULT_EMAIL_WIDGET)
    email2 = forms.EmailField(required=True, label="Email Confirmation",
                              help_text="Enter the same email as above, for verification.",
                              widget=DEFAULT_EMAIL_WIDGET)
    on_mailing_list = forms.BooleanField(label=SUBSCRIBE_TO_MAILING_LIST_LABEL, initial=False, required=False,
                                         help_text=SUBSCRIBE_TO_MAILING_LIST_HELP)

    def __init__(self, *args, **kwargs):
        super(CustomerCreationForm, self).__init__(*args, **kwargs)
        # the username field won't be displayed on the form, it will be given a default (generated) value
        self.fields['username'].required = False
        self.fields['password1'].widget = DEFAULT_PASSWORD_WIDGET
        self.fields['password2'].widget = DEFAULT_PASSWORD_WIDGET
        self.fields['password2'].label = "Retype Password"
        self.fields['email2'].label = "Retype Email"
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
                else:
                    # only the count the error against the username field if it's not a uniqueness kind of error
                    raise e
        else:
            # the email field is invalid, so don't even bother cleaning the username, there's no way it could be legit
            return None

    def save(self, commit=True):
        user = super(CustomerCreationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            on_mailing_list = self.cleaned_data.get('on_mailing_list', False)
            if on_mailing_list:
                item = EmailListItem(email=user.email, first_name=user.first_name)
                try:
                    item.full_clean()
                    item.save()
                except Exception, e:
                    logger.error('Failed to add new user to mailing list', e)
        return user


class CustomerAuthenticationForm(AuthenticationForm):

    email = forms.EmailField(required=True, widget=DEFAULT_EMAIL_WIDGET)

    def __init__(self, *args, **kwargs):
        super(CustomerAuthenticationForm, self).__init__(*args, **kwargs)
        self.fields['username'].required = False
        self.fields['password'].widget = DEFAULT_PASSWORD_WIDGET
        self.fields.keyOrder = ['email', 'password', 'username']
        self.error_messages['invalid_login'] = u'Incorrect email/password combination. Note that both fields are case sensitive.'

    def clean_username(self):
        email = self.cleaned_data.get('email', '')
        if email:
            return username_from_email(email)
        return ''


class CreatePublicProfileForm(forms.Form):
    username = forms.CharField(label="Pseudonym", max_length=PublicProfile.NAME_LENGTH, validators=[not_blank],
                               help_text="%d characters max, including spaces" % PublicProfile.NAME_LENGTH,
                               widget=DEFAULT_PROFILE_USERNAME_WIDGET)
    description = forms.CharField(max_length=PublicProfile.DESCRIPTION_LENGTH, required=False,
                                  help_text="Describe yourself in %d characters or less.  "
                                            "Example: 'artist and mother of two'" % PublicProfile.DESCRIPTION_LENGTH,
                                  widget=forms.Textarea(attrs={'maxlength': PublicProfile.DESCRIPTION_LENGTH,
                                                               'rows': 3, 'cols': 40}))
    location = forms.CharField(max_length=PublicProfile.LOCATION_LENGTH, required=False,
                               help_text="Examples: 'Edmonton, AB' or 'Saskatchewan'",
                               widget=forms.TextInput(attrs={'size': 40, 'maxlength': PublicProfile.LOCATION_LENGTH}))

    def __init__(self, request, *args, **kwargs):
        super(CreatePublicProfileForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        data = super(CreatePublicProfileForm, self).clean()
        if not self.request.user.is_authenticated():
            raise ValidationError(u"You must be logged-in to create a public profile.")
        return data

    def clean_username(self):
        username = self.cleaned_data.get('username', None)
        if username and PublicProfile.objects.filter(username=username).exclude(user=self.request.user).exists():
            raise ValidationError(u"Sorry, this pseudonym is already taken")
        return username

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

    first_name = forms.CharField(max_length=30, required=True, widget=DEFAULT_NAME_WIDGET)  # 30 is the max length set by User
    last_name = forms.CharField(max_length=30, required=True, widget=DEFAULT_NAME_WIDGET)   # 30 is the max length set by User
    email = forms.EmailField(required=True, widget=DEFAULT_EMAIL_WIDGET)
    email2 = forms.EmailField(required=True, label="Retype Email", widget=DEFAULT_EMAIL_WIDGET, help_text="Enter the same email as above, for verification.")
    contact_method = forms.ChoiceField(choices=CONTACT_METHOD_CHOICES, initial=CustomerProfile.EMAIL,
                                       widget=forms.RadioSelect,
                                       label="Preferred Contact Method?",
                                       help_text="We will never contact you personally unless there is a problem with your order.")
    phone = forms.CharField(max_length=20, widget=DEFAULT_PHONE_WIDGET, label="Daytime Phone")

    def __init__(self, request, *args, **kwargs):
        readonly_email = False
        if 'data' in kwargs and kwargs['data']:
            if request.user.is_authenticated() and request.user.email:
                # it's not a simple thing to change a register's user's email address, don't let them do that from
                # this form
                kwargs['data']['email'] = request.user.email
                kwargs['data']['email2'] = request.user.email
                readonly_email = True

        super(ContactInfoForm, self).__init__(*args, **kwargs)
        self.request = request
        if readonly_email:
            self.fields['email'].help_text = get_readonly_email_help()

    def clean_email2(self):
        email1 = self.cleaned_data.get('email', None)
        email2 = self.cleaned_data.get('email2', '')
        if email1 and email2 and email1 != email2:
            raise ValidationError(u"The two email addresses do not match.")
        return email2


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
                'phone': profile.phone
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
                                      "Examples: 'Me', 'Office'", validators=[not_blank],
                            widget=DEFAULT_NICKNAME_WIDGET)

    ship_to_me = forms.BooleanField(required=False, label="Ship to Me", initial=False)

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
        if self.customer:
            address.customer = self.customer
        if commit:
            address.full_clean()
            address.save()
        return address


class CustomerBillingAddressForm(BillingForm):
    """
    A billing address that is linked to a customer account.
    """

    def __init__(self, customer, *args, **kwargs):
        super(CustomerBillingAddressForm, self).__init__(*args, **kwargs)
        self.customer = customer

    def save(self, clazz, commit=True):
        address = super(CustomerBillingAddressForm, self).save(clazz, commit=False)
        if self.customer:
            address.customer = self.customer
        if commit:
            address.full_clean()
            address.save()
        return address


