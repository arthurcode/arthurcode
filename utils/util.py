__author__ = 'rhyanarthur'

from decimal import Decimal, ROUND_HALF_DOWN


def round_cents(dec_value):
    if not dec_value:
        return dec_value
    return dec_value.quantize(Decimal('.01'), rounding=ROUND_HALF_DOWN)