from django import forms
import utils
from accounts.forms import DEFAULT_EMAIL_WIDGET, DEFAULT_NAME_WIDGET, FIRST_NAME_MAXLENGTH


class SubscribeToMailingListForm(forms.Form):
    email = forms.EmailField(widget=DEFAULT_EMAIL_WIDGET)
    first_name = forms.CharField(max_length=FIRST_NAME_MAXLENGTH, required=False, widget=DEFAULT_NAME_WIDGET)

    def __init__(self, request, *args, **kwargs):
        super(SubscribeToMailingListForm, self).__init__(*args, **kwargs)
        self.request = request
        if self.request.user.is_authenticated():
            # pre-fill form fields for authenticated users
            self.fields['email'].initial = self.request.user.email
            self.fields['first_name'].initial = self.request.user.first_name

    def save(self):
        email = self.cleaned_data.get('email')
        first_name = self.cleaned_data.get('first_name', None)
        utils.add_to_list(email, first_name)