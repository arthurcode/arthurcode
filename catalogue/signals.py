from django.db.models.signals import post_save
from django.dispatch import receiver
from catalogue.models import Review
from django.core.mail import mail_managers
import django.dispatch
from difflib import Differ

review_edited = django.dispatch.Signal(providing_args=['original'])
review_deleted = django.dispatch.Signal()  # review deleted by user

@receiver(post_save, sender=Review)
def review_added(sender, **kwargs):
    """
    Notify site managers via email whenever a new review is added.
    """
    if not kwargs.get('created', True):
        # review modification is handled via a different signal
        return
    review = kwargs.get('instance')
    subject = "New Review: " + review.product.name
    mail_managers(subject, review.as_text())


@receiver(review_edited)
def handle_review_edited(sender, **kwargs):
    """
    Notify site managers via email whenever a review is edited.
    """
    original_review_text = kwargs.get('original')

    subject = "Review Edited: " + sender.product.name
    diffs = list(Differ().compare(original_review_text.splitlines(1), sender.as_text().splitlines(1)))
    mail_managers(subject, "".join(diffs))


@receiver(review_deleted)
def handle_review_deleted(sender, **kwargs):
    """
    Notify site managers when a user deletes one of his/her reviews.
    """
    subject = "Review Deleted: " + sender.product.name
    mail_managers(subject, sender.as_text())


