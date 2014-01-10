"""
Utility functions for working with mailing lists.
"""

from models import EmailListItem


def is_on_list(email):
    if email is None:
        return False
    return EmailListItem.objects.filter(email=email).exists()


def add_to_list(email):
    if EmailListItem.objects.filter(email=email).exists():
        return
    item = EmailListItem(email=email)
    item.full_clean()
    item.save()


def remove_from_list(email):
    items = EmailListItem.objects.filter(email=email)
    for item in items:
        # there should only be one item in the list, I'm just being paranoid
        item.delete()

