__author__ = 'rhyanarthur'

from decimal import Decimal, ROUND_HALF_DOWN
from django.contrib.sites.models import get_current_site


def round_cents(dec_value):
    if not dec_value:
        return dec_value
    return dec_value.quantize(Decimal('.01'), rounding=ROUND_HALF_DOWN)


def to_bool(value):
    if isinstance(value, bool):
        return value
    if value in ['True', 1, 'true', 't', 'T', 'TRUE']:
        return True
    return False


def get_full_url(instance, request=None):
    """
    Returns the full url of the given model instance, including the domain name.
    """
    if request:
        return request.build_absolute_uri(instance.get_absolute_url())
    # we don't have the request, use the Sites framework
    return 'http://' + get_current_site(None).domain + instance.get_absolute_url()