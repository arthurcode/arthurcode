"""
A module that collects all functions and classes related to on-site credit-card processing.
"""
from decimal import Decimal

DUMMY_TRANSACTION_ID = '0000000000'


def authorize(card_type, amount, billing_address):
    """
    Authorizes a credit-card charge and returns the transaction id, if successful.  At the moment this method is
    just a stub.  It will always return a transaction id of '000000000'.
    """
    return DUMMY_TRANSACTION_ID


def get_gift_card_balance(card_number):
    """
    Returns the balance of this card (if valid).  At the moment this method will always return $10.
    """
    return Decimal('10.00')
