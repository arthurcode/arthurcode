from django import forms
from accounts.models import CustomerProfile
from django.core.exceptions import ValidationError
import datetime
import re
from utils.forms import CanadaShippingForm


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

    def humanized_contact_method(self):
        """
        Return the human-readable contact-method string.  This must be called after the form has been validated otherwise
        an exception will be thrown.
        """
        my_method = self.cleaned_data['contact_method']
        for method in CustomerProfile.CONTACT_METHOD:
            if method[0] == int(my_method):
                return method[1]
        return "Unknown"


class PaymentInfoForm(forms.Form):
    card_type = forms.ChoiceField(choices=CARD_TYPES, widget=forms.RadioSelect, label='Card Type')
    card_number = forms.CharField(label='Card Number')
    expire_month = forms.ChoiceField(choices=cc_expire_months(), label='Month')
    expire_year = forms.ChoiceField(choices=cc_expire_years(), label='Year')
    cvv = forms.CharField(label='CVV', max_length=4,
                          help_text="<a href='http://www.cvvnumber.com/cvv.html' target='_blank' style='font-size:11px'>What is my CVV code?</a>")  # most are 3 digits, american-express is 4 digits
    total = forms.DecimalField(decimal_places=2, max_digits=9, widget=forms.HiddenInput, min_value=0.00)

    def clean_card_number(self):
        cc_number = self.cleaned_data.get('card_number', None)
        if cc_number:
            cc_number = strip_non_numbers(cc_number)
            if not cardLuhnChecksumIsValid(cc_number):
                raise forms.ValidationError('The credit card number you entered is invalid.')
        return cc_number

    def clean_cvv(self):
        error = u'Please enter a valid CVV code.'
        cvv = self.cleaned_data.get('cvv', None)
        if cvv:
            try:
                code = int(cvv)
                if code < 0:
                    raise ValidationError(error)
            except ValueError:
                raise ValidationError(error)
        return cvv


class ChooseAddressForm(forms.Form):
    """
    An address that can be chosen and validated against an existing AddressForm class.
    """
    address_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, address, form_clazz, *args, **kwargs):
        super(ChooseAddressForm, self).__init__(*args, **kwargs)
        self.address = address
        self.form_clazz = form_clazz
        self.fields['address_id'].initial = address.id

    def clean(self):
        data = {
            'name': self.address.name,
            'phone': self.address.phone,
            'line1': self.address.line1,
            'line2': self.address.line2,
            'city': self.address.city,
            'region': self.address.region,
            'post_code': self.address.post_code,
            'country': self.address.country
        }
        form = self.form_clazz(data=data)
        if form.is_valid():
            return
        #TODO: transfer the errors from form to self
        self._errors = form._errors