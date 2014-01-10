"""
Utility functions for working with mailing lists.
"""

from models import EmailListItem


def is_on_list(email):
    if email is None:
        return False
    return EmailListItem.objects.filter(email=email).exists()


def add_to_list(email, first_name=None):
    if EmailListItem.objects.filter(email=email).exists():
        return
    item = EmailListItem(email=email, first_name=first_name)
    item.full_clean()
    item.save()


def remove_from_list(email):
    items = EmailListItem.objects.filter(email=email)
    for item in items:
        # there should only be one item in the list, I'm just being paranoid
        item.delete()


def handle_change_of_email(old_email, new_email):
    if old_email:
        try:
            item = EmailListItem.objects.get(email=old_email)
            item.email = new_email
            item.full_clean()
            item.save()
        except EmailListItem.DoesNotExist:
            return