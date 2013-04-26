from django import forms
from models import AbstractAddress
from django.contrib.localflavor.ca.forms import CAPhoneNumberField, CAPostalCodeField, CAProvinceSelect, CAProvinceField


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