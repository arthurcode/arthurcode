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
    mail_managers(subject, review_as_text(review))


@receiver(review_edited)
def handle_review_edited(sender, **kwargs):
    """
    Notify site managers via email whenever a review is edited.
    """
    original_review_text = kwargs.get('original')

    subject = "Review Edited: " + sender.product.name
    diffs = list(Differ().compare(original_review_text.splitlines(1), review_as_text(sender).splitlines(1)))
    mail_managers(subject, "".join(diffs))


@receiver(review_deleted)
def handle_review_deleted(sender, **kwargs):
    """
    Notify site managers when a user deletes one of his/her reviews.
    """
    subject = "Review Deleted: " + sender.product.name
    mail_managers(subject, review_as_text(sender, include_url=False))


def review_as_text(review, include_url=True):
    text = """
    name:    %s
    rating:  %d
    summary: %s

    %s

    """ % (review.user.public_name() or "anonymous user",
           review.rating,
           review.summary,
           review.review or "(reviewer did not provide details)")

    if include_url:
        text += "link: " + review.get_absolute_url()
    return text


