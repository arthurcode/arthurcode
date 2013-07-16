"""
Contains signals related to Order management
"""

import django.dispatch
from django.dispatch import receiver

signal_order_cancelled = django.dispatch.Signal()

@receiver(signal_order_cancelled)
def order_cancelled(sender, **kwargs):
    """
    Email the site managers/admins when an order is cancelled.  Send an email to the customer indicating that their
    order has been cancelled.
    """
    pass



