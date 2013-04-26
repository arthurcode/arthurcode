from django import forms
from models import AbstractAddress


class CanadaShippingForm(forms.Form):
    name = forms.CharField(max_length=AbstractAddress.ADDRESSEE_LENGTH, label="Recipient's Full Name")
    phone = forms.CharField(max_length=AbstractAddress.PHONE_NUMBER_LENGTH, label="Recipient's Phone Number",
                            help_text='This is required by some shipping companies.')
    line1 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 1")
    line2 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 2", required=False)
    city = forms.CharField(max_length=AbstractAddress.CITY_LENGTH, label="City/Town")
    province = forms.CharField(max_length=AbstractAddress.REGION_LENGTH, label="Province")
    postal_code = forms.CharField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Postal Code")