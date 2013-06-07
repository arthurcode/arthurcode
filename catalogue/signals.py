from django.db.models.signals import post_save
from django.dispatch import receiver
from catalogue.models import Review
from django.core.mail import mail_managers
import django.dispatch
from difflib import Differ

review_edited = django.dispatch.Signal(providing_args=['original'])

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


def review_as_text(review):
    return """
    name:    %s
    rating:  %d
    summary: %s
    link:    %s

    %s
    """ % (review.user.public_name() or "anonymous user",
           review.rating,
           review.summary,
           review.get_absolute_url(),
           review.review or "(reviewer did not provide details)")


