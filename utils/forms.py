from django import forms
from models import AbstractAddress
from django.contrib.localflavor.ca.forms import CAPhoneNumberField, CAPostalCodeField, CAProvinceSelect, CAProvinceField
from django_countries import countries


# display as an optgroup with commonly selected countries at the top
COUNTRY_CHOICES = [
    ("", ((u'CA', u'Canada'),
          (u'US', u'United States'),)),
    (u"All Countries", countries.COUNTRIES)
]


class CanadaShippingForm(forms.Form):
    name = forms.CharField(max_length=AbstractAddress.ADDRESSEE_LENGTH, label="Recipient's Full Name")
    phone = CAPhoneNumberField(label="Recipient's Phone Number",
                                     help_text='(Example: 403-555-7777) This is required by some shipping companies.')
    line1 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 1")
    line2 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 2", required=False)
    city = forms.CharField(max_length=AbstractAddress.CITY_LENGTH, label="City/Town")
    province = CAProvinceField(widget=CAProvinceSelect)
    postal_code = CAPostalCodeField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Postal Code",
                                    help_text='(Example: T1B 2K9)')

class BillingForm(forms.Form):
    name = forms.CharField(max_length=AbstractAddress.ADDRESSEE_LENGTH, label="Name",
                           help_text="Full name as it appears on your credit card.")
    line1 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 1")
    line2 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 2", required=False)
    city = forms.CharField(max_length=AbstractAddress.CITY_LENGTH, label="City/Town")
    region = forms.CharField(max_length=AbstractAddress.REGION_LENGTH, label="State/Province")
    postal_code = forms.CharField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Zip/Postal Code")
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, label="Country")