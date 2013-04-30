from django import forms
from accounts.models import CustomerProfile
from django.contrib.formtools.wizard.views import SessionWizardView
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from utils.forms import CanadaShippingForm, BillingForm
import datetime
import re


def cc_expire_years():
    current_year = datetime.datetime.now().year
    years = range(current_year, current_year + 12)
    return [(str(x), str(x)) for x in years]


def cc_expire_months():
    months = []
    for month in range(1,13):
        if len(str(month)) == 1:
            numeric = '0' + str(month)
        else:
            numeric = str(month)
        months.append((numeric, datetime.date(2009, month, 1).strftime('%B')))
    return months


CARD_TYPES = (
    ('Mastercard', 'Mastercard'),
    ('VISA', 'VISA'),
    ('AMEX', 'AMEX'),
    ('Discover', 'Discover'),)


NON_NUMBERS = re.compile('\D')


def strip_non_numbers(data):
    return NON_NUMBERS.sub('', data)


def cardLuhnChecksumIsValid(card_number):
    """
    Checks to make sure the card passes a luhn mod-10 checksum
    """
    checksum = 0
    num_digits = len(card_number)
    oddeven = num_digits & 1
    for count in range(0, num_digits):
        digit = int(card_number[count])
        if not ((count & 1) ^ oddeven):
            digit *= 2
        if digit > 9:
            digit -= 9
        checksum += digit
    return (checksum % 10) == 0


class ContactInfoForm(forms.Form):

    ERROR_PHONE_REQUIRED = u"A phone number is required because you selected 'Phone' as your preferred contact method."

    first_name = forms.CharField(max_length=30, required=True)  # 30 is the max length set by User
    last_name = forms.CharField(max_length=30, required=True)   # 30 is the max length set by User
    email = forms.EmailField(required=True)
    email2 = forms.EmailField(required=True, label="Retype Email")
    contact_method = forms.ChoiceField(choices=CustomerProfile.CONTACT_METHOD, initial=CustomerProfile.EMAIL,
                                       widget=forms.RadioSelect,
                                       label="If there is a problem with your order how should we contact you?")
    phone = forms.CharField(max_length=20, required=False)

    def clean_email2(self):
        email1 = self.cleaned_data.get('email', None)
        email2 = self.cleaned_data.get('email2', '')
        if email1 and email2 and email1 != email2:
            raise ValidationError(u"The two email addresses do not match.")
        return email2

    def clean(self):
        cleaned_data = super(ContactInfoForm, self).clean()
        contact_method = cleaned_data.get('contact_method', None)

        if contact_method and int(contact_method) == CustomerProfile.PHONE and not 'phone' in self.changed_data:
            # a phone number wasn't entered, indicate that it is now conditionally required.
            self._errors['contact_method'] = self.error_class([ContactInfoForm.ERROR_PHONE_REQUIRED])
            self._errors['phone'] = self.error_class([ContactInfoForm.ERROR_PHONE_REQUIRED])
            del(cleaned_data['contact_method'])

        return cleaned_data


class PaymentInfoForm(forms.Form):
    card_type = forms.ChoiceField(choices=CARD_TYPES, widget=forms.RadioSelect, label='Card Type')
    card_number = forms.CharField(label='Card Number')
    expire_month = forms.ChoiceField(choices=cc_expire_months(), label='Month')
    expire_year = forms.ChoiceField(choices=cc_expire_years(), label='Year')
    cvv = forms.CharField(label='cvv')

    def clean_card_number(self):
        cc_number = self.cleaned_data.get('card_number', None)
        if cc_number:
            cc_number = strip_non_numbers(cc_number)
            if not cardLuhnChecksumIsValid(cc_number):
                raise forms.ValidationError('The credit card number you entered is invalid.')
        return cc_number

class OrderWizard(SessionWizardView):

    FORMS = [
        ('contact', ContactInfoForm),
        ('shipping', CanadaShippingForm),
        ('billing', BillingForm),
        ('payment', PaymentInfoForm)
    ]

    TEMPLATES = {
        'contact': 'contact_info.html',
        'shipping': 'shipping_form.html',
        'billing': 'billing_form.html',
        'payment': 'review_and_pay.html'
    }

    def get_template_names(self):
        return [OrderWizard.TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        # TODO CHANGE THIS OF COURSE!
        return HttpResponseRedirect(reverse('show_account'))


