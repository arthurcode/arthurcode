from django.db.models.signals import post_save
from django.dispatch import receiver
import django.dispatch
from reviews.models import Review
from reviews import email

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
    email.notify_managers_new_review(review)


@receiver(review_edited)
def handle_review_edited(sender, **kwargs):
    """
    Notify site managers via email whenever a review is edited.
    """
    original_review_text = kwargs.get('original')
    email.notify_managers_review_edited(sender, original_review_text)


@receiver(review_deleted)
def handle_review_deleted(sender, **kwargs):
    """
    Notify site managers when a user deletes one of his/her reviews.
    """
    email.notify_managers_review_deleted(sender)


