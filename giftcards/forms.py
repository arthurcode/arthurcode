from django import forms
from giftcards.validators import validate_gc_number
from decimal import Decimal

DEFAULT_GC_WIDGET = forms.TextInput(attrs={'size': 19, 'maxlength': 25})
DEFAULT_GC_VALUE_WIDGET = forms.TextInput(attrs={'size': 3, 'maxlength': 3})


class CheckBalanceForm(forms.Form):

    number = forms.CharField(label='Gift Card Number', widget=DEFAULT_GC_WIDGET, validators=[validate_gc_number],
                             help_text='Your 16 digit gift card number, XXXX XXXX XXXX XXXX')

    def check_balance(self):
        # TODO: actually check the balance
        return Decimal('25')