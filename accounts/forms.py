from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
import hashlib
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from utils.validators import not_blank
from accounts.models import PublicProfile


def username_from_email(email):
    md5 = hashlib.md5(email.lower())
    return md5.hexdigest()[:30]  # max 30 characters


class CustomerCreationForm(UserCreationForm):
    """
    A user creation form that requires an email instead of a username.  We attempt to generate a unique username
    from the email address using an md5 hash algorithm.
    """
    first_name = forms.CharField(max_length=30, required=True, validators=[not_blank])
    last_name = forms.CharField(max_length=30, required=True, validators=[not_blank])
    email = forms.EmailField(required=True)

    def __init__(self, *args, **kwargs):
        super(CustomerCreationForm, self).__init__(*args, **kwargs)
        # the username field won't be displayed on the form, it will be given a default (generated) value
        self.fields['username'].required = False
        # make sure the username is cleaned last, since it depends on email
        self.fields.keyOrder = ['email', 'password1', 'password2', 'first_name', 'last_name', 'username']

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
        user = super(CustomerCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


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
        super(CreatePublicProfileForm, self).clean()
        if not self.request.user.is_authenticated():
            raise ValidationError(u"You must be logged-in to create a public profile.")

    def create_profile(self, commit=True):
        profile = PublicProfile(user=self.request.user)
        profile.username = self.data['username']
        profile.description = self.data['description']
        profile.location = self.data['location']

        if commit:
            profile.full_clean()
            profile.save()
        return profile


