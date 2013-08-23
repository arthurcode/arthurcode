from django import forms
from models import AbstractAddress
from django.contrib.localflavor.ca.forms import CAPhoneNumberField, CAPostalCodeField, CAProvinceSelect, CAProvinceField
from django_countries import countries
from django.core.exceptions import ValidationError

DEFAULT_ADDRESSEE_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength':AbstractAddress.ADDRESSEE_LENGTH})
DEFAULT_ADDRESSEE_PHONE_WIDGET = forms.TextInput(attrs={'size': 12, 'maxlength': AbstractAddress.PHONE_NUMBER_LENGTH})
DEFAULT_ADDRESS_LINE_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength': AbstractAddress.LINE_LENGTH})
DEFAULT_CITY_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength': AbstractAddress.CITY_LENGTH})
DEFAULT_REGION_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength': AbstractAddress.REGION_LENGTH})
DEFAULT_POST_WIDGET = forms.TextInput(attrs={'size': 7, 'maxlength':AbstractAddress.POST_CODE_LENGTH})

# display as an optgroup with commonly selected countries at the top
COUNTRY_CHOICES = [
    ("", ((u'CA', u'Canada'),
          (u'US', u'United States'),)),
    (u"All Countries", countries.COUNTRIES)
]


class AddressForm(forms.Form):
    """
    The DB requires that the address line1, city, region and country fields not be non-null.
    """
    name = forms.CharField(max_length=AbstractAddress.ADDRESSEE_LENGTH, label="Name", required=False,
                           widget=DEFAULT_ADDRESSEE_WIDGET,
                           help_text="Recipient's full name.<br>Example: John Smith")
    phone = forms.CharField(max_length=AbstractAddress.PHONE_NUMBER_LENGTH, label="Phone (day)", required=False,
                            widget=DEFAULT_ADDRESSEE_PHONE_WIDGET,
                            help_text="Recipient's day-time phone number. This is required by some shipping companies.")
    line1 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 1", widget=DEFAULT_ADDRESS_LINE_WIDGET)
    line2 = forms.CharField(max_length=AbstractAddress.LINE_LENGTH, label="Address Line 2", widget=DEFAULT_ADDRESS_LINE_WIDGET, required=False)
    city = forms.CharField(max_length=AbstractAddress.CITY_LENGTH, label="City/Town", widget=DEFAULT_CITY_WIDGET)
    region = forms.CharField(max_length=AbstractAddress.REGION_LENGTH, label="State/Province", widget=DEFAULT_REGION_WIDGET)
    post_code = forms.CharField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Zip/Postal Code", required=False, widget=DEFAULT_POST_WIDGET)
    country = forms.ChoiceField(choices=COUNTRY_CHOICES, label="Country")
    address_id = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, address_id=None, *args, **kwargs):
        if address_id:
            initial = kwargs.get('initial', {}) or {}
            initial['address_id'] = address_id
            kwargs['initial'] = initial
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

        address_id = self.cleaned_data.get('address_id', None)
        if address_id:
            # we're editing an existing address
            address = clazz.objects.get(id=address_id)
        else:
            address = clazz()

        # set fields
        address.name = cd['name']
        address.phone = cd['phone']
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
        field.required = True

    def customize_phone(self, field):
        self.fields['phone'] = CAPhoneNumberField(label=field.label, required=True,
                                                  help_text=field.help_text,
                                                  widget=DEFAULT_ADDRESSEE_PHONE_WIDGET)

    def customize_region(self, field):
        self.fields['region'] = CAProvinceField(widget=CAProvinceSelect, label="Province")

    def customize_post_code(self, field):

        self.fields['post_code'] = CAPostalCodeField(max_length=AbstractAddress.POST_CODE_LENGTH, label="Postal Code",
                                    required=True, widget=DEFAULT_POST_WIDGET)

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

    same_as_shipping = forms.BooleanField(required=False, label="Same as shipping address", initial=False)

    def customize_name(self, field):
        field.required = True

    def customize_post_code(self, field):
        field.required = True
