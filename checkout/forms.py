from django import forms
from accounts.models import CustomerProfile
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


class ContactInfoForm(forms.Form):

    ERROR_PHONE_REQUIRED = u"A phone number is required because you selected 'Phone' as your preferred contact method."

    first_name = forms.CharField(max_length=30, required=True)  # 30 is the max length set by User
    last_name = forms.CharField(max_length=30, required=True)   # 30 is the max length set by User
    email = forms.EmailField(required=True)
    contact_method = forms.ChoiceField(choices=CustomerProfile.CONTACT_METHOD, initial=CustomerProfile.EMAIL,
                                       widget=forms.RadioSelect,
                                       label="If there is a problem with your order how should we contact you?")
    phone = forms.CharField(max_length=20, required=False)

    def clean(self):
        cleaned_data = super(ContactInfoForm, self).clean()
        contact_method = cleaned_data.get('contact_method', None)

        if contact_method and int(contact_method) == CustomerProfile.PHONE and not 'phone' in self.changed_data:
            # a phone number wasn't entered, indicate that it is now conditionally required.
            self._errors['contact_method'] = self.error_class([ContactInfoForm.ERROR_PHONE_REQUIRED])
            self._errors['phone'] = self.error_class([ContactInfoForm.ERROR_PHONE_REQUIRED])
            del(cleaned_data['contact_method'])

        return cleaned_data


class OrderWizard(SessionWizardView):

    FORMS = [
        ('contact', ContactInfoForm)
    ]

    TEMPLATES = {
        'contact': 'contact_info.html'
    }

    def get_template_names(self):
        return [OrderWizard.TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        # TODO CHANGE THIS OF COURSE!
        return HttpResponseRedirect(reverse('show_account'))



