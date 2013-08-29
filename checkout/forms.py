import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from utils.forms import add_empty_choice
from orders.models import CreditCardPayment
from credit_card import authorize, get_gift_card_balance
from utils.validators import not_blank


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
        #months.append((numeric, datetime.date(2009, month, 1).strftime('%B')))
        months.append((numeric, numeric))
    return months


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


class PaymentInfoForm(forms.Form):
    card_type = forms.ChoiceField(choices=CreditCardPayment.CARD_TYPES, widget=forms.RadioSelect, label='Credit Card Type')
    card_number = forms.CharField(label='Card Number', widget=forms.TextInput(attrs={'size': 19, 'maxlength': 25}))
    expire_month = forms.ChoiceField(choices=add_empty_choice(cc_expire_months(), '-'), label='Month')
    expire_year = forms.ChoiceField(choices=add_empty_choice(cc_expire_years(), '-'), label='Year')
    cvv = forms.CharField(label='CVV', max_length=3,
                          help_text="<a href='http://www.cvvnumber.com/cvv.html' target='_blank' style='font-size:11px'>What is my CVV code?</a>",
                          widget=forms.TextInput(attrs={'size': 3, 'maxlength': 3}))  # most are 3 digits, american-express is 4 digits

    def __init__(self, pyOrder, amount, *args, **kwargs):
        self.pyOrder = pyOrder
        self.amount = amount
        super(PaymentInfoForm, self).__init__(*args, **kwargs)

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

    def clean(self):
        cd = super(PaymentInfoForm, self).clean()
        # authorize the funds
        self.transaction_id = authorize(cd['card_type'], self.amount, self.pyOrder.billing_address)
        return cd


class AddGiftCardForm(forms.Form):
    card_number = forms.CharField(label='Gift Card Number', widget=forms.TextInput(attrs={'size': 19, 'maxlength': 25}),
                                  validators=[not_blank])

    def __init__(self, *args, **kwargs):
        super(AddGiftCardForm, self).__init__(*args, **kwargs)

    def clean_card_number(self):
        number = self.cleaned_data.get('card_number', None)
        if number:
            number = strip_non_numbers(number)
            if not len(number) == 16:
                raise ValidationError(u"Card numbers are exactly 16 digits long")
            balance = get_gift_card_balance(number)
            if balance is None:
                raise ValidationError(u"Sorry, this is an unrecognized gift card number.")
            if balance <= 0:
                raise ValidationError(u"Sorry, there is no money left on this card.")
        return number


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


class ChooseShippingAddressByNickname(forms.Form):
    """
    Chooses from a set of existing shipping addresses by nickname.
    """
    ME_NICKNAME = "Me"
    NEW_ADDRESS_NICKNAME = "New Address"
    SHIP_TO_KEY = "ship_to"

    def __init__(self, request, *args, **kwargs):
        self.request = request
        super(ChooseShippingAddressByNickname, self).__init__(*args, **kwargs)
        nicknames = self.get_existing_nicknames()
        nicknames.sort()

        # the choices group always has to start with 'Me'
        choices = []
        address_book_choices = [(self.ME_NICKNAME, self.ME_NICKNAME)]
        address_book_choices.extend([(n, n) for n in nicknames if n != self.ME_NICKNAME])
        choices.append(("Address Book", address_book_choices))
        choices.append(("Other", ((self.NEW_ADDRESS_NICKNAME, 'New Address'),)))

        self.fields[self.SHIP_TO_KEY] = forms.ChoiceField(choices=choices, widget=forms.Select,
                                                                               label="Ship To", required=True)
        if kwargs and 'initial' in kwargs and self.SHIP_TO_KEY in kwargs['initial']:
            self.fields[self.SHIP_TO_KEY].initial = kwargs['initial'][self.SHIP_TO_KEY]

    def get_existing_nicknames(self):
        """
        Returns the nicknames that identify this customer's saved shipping addresses.  Returns and empty list if the
        customer doesn't have a profile or if there aren't any addresses associated with the profile.
        """
        profile = self.request.user.get_customer_profile()
        if not profile:
            return []
        return [a.nickname for a in profile.shipping_addresses.all()]