"""
Collects all of the email sent by the review app into one file.
"""

from django.core.mail import EmailMessage, mail_managers, send_mail
from arthurcode import settings
from utils.util import get_full_url
from django.core.urlresolvers import reverse

EMAIL_AUTHOR_REVIEW_DELETED_BY_ADMIN = """
Your review for product '%(product)s' has been deleted for the following reason(s):

    %(reason)s

Click the following link to log-in and write a new review that adheres to our review guidelines:
%(link)s

Sincerely,

%(site-name)s Admin

----------- ORIGINAL REVIEW --------------

%(review)s
"""

EMAIL_MANAGEMENT_REVIEW_DELETED_BY_ADMIN = """
The following review for product '%(product)s' was deleted by staff-member %(staff)s:

    %(review)s

REASON:

    %(reason)s
"""


def get_template_data():
    return {
        'site-name': settings.SITE_NAME
    }


def notify_managers_review_deleted_by_admin(request, review, reason):
    subject = "Review Deleted by Staff Member"
    data = get_template_data()
    data.update({
        'product': review.product,
        'reason': reason,
        'review': review.as_text(),
        'staff': request.user.username
    })
    content = EMAIL_MANAGEMENT_REVIEW_DELETED_BY_ADMIN % data
    mail_managers(subject, content)


def notify_author_review_deleted_by_admin(request, review, reason):
    subject = "Your Review was Deleted"
    data = get_template_data()
    data.update({
        'product': review.product,
        'reason': reason,
        'review': review.as_text(),
        'link': get_full_url(reverse('product_review', kwargs={'product_slug': review.product.slug}), request)
    })
    content = EMAIL_AUTHOR_REVIEW_DELETED_BY_ADMIN % data
    recipients = [review.user.email]
    bcc = [email for (_, email) in settings.MANAGERS]
    email = EmailMessage(subject, content, to=recipients, bcc=bcc)
    email.send()

