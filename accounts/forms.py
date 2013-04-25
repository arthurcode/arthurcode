from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django import forms
import hashlib
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from utils.validators import not_blank


def username_from_email(email):
    md5 = hashlib.md5(email.lower())
    return md5.hexdigest()[:30]  # max 30 characters


class CustomerCreationForm(UserCreationForm):
    """
    A user creation form that requires an email instead of a username.  We attempt to generate a unique username
    from the email address using an md5 hash algorithm.
    """
    first_name = forms.CharField(max_length=30, required=True, validators=[not_blank])
    last_name = forms.CharField(max_length=30, required=False)
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
                    try:
                        User.objects.get(email=email)
                        self.errors['email'] = self.error_class([u'A user with this email address already exists.'])
                    except User.DoesNotExist:
                        # hmmm, this must be a hash algorithm collision
                        self.errors['email'] = self.error_class([u'Sorry, we were unable to generate a unique username from '
                                                                 u'this email address. You will need to register with'
                                                                 u' a different email address.'])
                raise e
        else:
            return super(CustomerCreationForm, self).clean_username()

    def clean_last_name(self):
        """
        Strip whitespace from the beginning and end of the last name (to avoid putting blank strings in the database)
        """
        name = self.data.get('last_name', '')
        if name:
            # Don't store strings of pure whitespace in the database
            name = name.strip()
        return name

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

