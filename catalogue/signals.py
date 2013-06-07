from django.db.models.signals import post_save
from django.dispatch import receiver
from catalogue.models import Review
from django.core.mail import mail_managers

@receiver(post_save, sender=Review)
def review_added(sender, **kwargs):
    """
    Notify site admins via email whenever a new review is added.
    """
    if not kwargs.get('created', True):
        return
    review = kwargs.get('instance')
    subject = "New Review: " + review.product.name
    mail_managers(subject, review_as_text(review))


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


