from django.contrib.auth.forms import UserCreationForm
from django import forms
import hashlib
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User


class CustomerCreationForm(UserCreationForm):
    """
    A user creation form that requires an email instead of a username.  We attempt to generate a unique username
    from the email address using an md5 hash algorithm.
    """
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        # make sure the username field is the last to be cleaned
        fields = ('email', 'password1', 'password2', 'first_name', 'last_name', 'username')

    def __init__(self, *args, **kwargs):
        super(CustomerCreationForm, self).__init__(*args, **kwargs)
        # the username field won't be displayed on the form, it will be given a default (generated) value
        self.fields['username'].required = False

    def clean_username(self):
        """
        Set the username to be the first 30 (of 32) characters of the md5 hash of the lower-case email address.
        Collisions are possible, but should be rare (I hope).
        """
        email = self.cleaned_data.get('email', None)
        if email:
            md5 = hashlib.md5(email.lower())
            self.cleaned_data['username'] = md5.hexdigest()[:30]
        try:
            return super(CustomerCreationForm, self).clean_username()
        except ValidationError, e:
            if unicode(self.error_messages['duplicate_username']) in unicode(e):
                # the generated username is not unique
                try:
                    User.objects.filter(email=email)
                    self.errors['email'] = self.error_class([u'A user with this email address already exists.'])
                except User.DoesNotExist:
                    # hmmm, this must be a hash algorithm collision
                    self.errors['email'] = self.error_class([u'Sorry, we were unable to generate a unique username from '
                                                             u'this email address. You will need to register with'
                                                             u' a different email address.'])
            raise e

    def save(self, commit=True):
        user = super(CustomerCreationForm, self).save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user