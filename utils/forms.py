from django import forms
from models import AbstractAddress
from django.contrib.localflavor.ca.forms import CAPhoneNumberField, CAPostalCodeField, CAProvinceSelect, CAProvinceField
from django_countries import countries
from utils.models import AbstractAddress
from django.core.exceptions import ValidationError


# display as an optgroup with commonly selected countries at the top
COUNTRY_CHOICES = [
    ("", ((u'CA', u'Canada'),
          (u'US', u'United States'),)),
    (u"All Countries", countries.COUNTRIES)
]


class AddressForm(forms.Form):
    """
    The DB requires that the name, address line1, and country fields be non-null.
    """
    name = forms.CharField(max_length=AbstractAddress.ADDRESSEE_LENGTH, label="Name")
    phone = forms.CharField(max_length=AbstractAddress.PHONE_NUMBER_LENGTH, label="Phone", required=False)
    line1 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 1")
    line2 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 2", required=False)
    city = forms.CharField(max_length=AbstractAddress.CITY_LENGTH, label="City/Town")
    region = forms.CharField(max_length=AbstractAddress.REGION_LENGTH, label="State/Province")
    post_code = forms.CharField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Zip/Postal Code")
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, label="Country")

    def __init__(self, *args, **kwargs):
        super(AddressForm, self).__init__(*args, **kwargs)
        for field in self.fields.keys():
            customize_method = 'customize_' + field
            if hasattr(self, customize_method):
                customize = getattr(self, customize_method)
                customize(self.fields[field])

    def save(self, clazz, commit=True):
        cd = self.cleaned_data
        if not issubclass(clazz, AbstractAddress):
            raise Exception("The AddressForm meta class is not a subclass of " + AbstractAddress.__class__.__name___)
        address = clazz()
        address.name = cd['name']
        address.phone_number = cd['phone']
        address.line1 = cd['line1']
        address.line2 = cd['line2']
        address.city = cd['city']
        address.region = cd['region']
        address.post_code = cd['post_code']
        address.country = cd['country']
        if commit:
            address.save()
        return address


class CanadaShippingForm(AddressForm):

    def customize_name(self, field):
        field.label = "Recipient's Full Name"

    def customize_phone(self, field):
        self.fields['phone'] = CAPhoneNumberField(label="Recipient's Phone Number", required=True,
                                                  help_text="This is required by some shipping companies.")

    def customize_region(self, field):
        self.fields['region'] = CAProvinceField(widget=CAProvinceSelect, label="Province")

    def customize_post_code(self, field):
        self.fields['post_code'] = CAPostalCodeField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Postal Code",
                                     help_text='(Example: T1B 2K9)')

    def customize_country(self, field):
        field.widget = forms.HiddenInput()
        field.initial = "CA"

    def clean_country(self):
        country = self.cleaned_data.get('country', None)
        if country and not country == "CA":
            raise ValidationError("Sorry, we can only ship to Canadian addresses.")

    def save(self, clazz, commit=True):
        # it's a little unreliable to use cleaned_data to capture the value of the 'country' field.  Since it's hidden
        # and has an initial value, it will not show up in the changed_data dict and thus won't have an entry in
        # cleaned data.  If we're building an address from this form, and the form had been validated then we can assume
        # that country is 'Canada'.
        address = super(CanadaShippingForm, self).save(clazz, commit=False)
        address.country = "CA"
        if commit:
            address.save()
        return address


class BillingForm(AddressForm):
    def customize_name(self, field):
        field.help_text = "Full name as it appears on your credit card."