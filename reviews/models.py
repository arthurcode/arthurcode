import datetime
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models

# Create your models here.
from catalogue.models import Product
from utils.util import get_full_url
from utils.validators import not_blank
from utils.models import AkismetMixin


class Review(models.Model, AkismetMixin):
    SUMMARY_LENGTH = 100

    RATING_CHOICES = (
        (5, '5 stars'),
        (4, '4 stars'),
        (3, '3 stars'),
        (2, '2 stars'),
        (1, '1 star')
    )

    product = models.ForeignKey(Product, related_name="reviews")
    user = models.ForeignKey(User)
    rating = models.IntegerField(choices=RATING_CHOICES)
    summary = models.CharField(max_length=SUMMARY_LENGTH, validators=[not_blank])
    review = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return self.product.get_absolute_url() + '#' + self.anchor

    def was_edited(self):
        """
        Returns true if the 'date_added' and 'last_modified' fields differ by 1 day or more.
        """
        delta = datetime.timedelta(days=1)
        return self.last_modified >= self.date_added + delta

    def is_flagged_for_removal(self):
        return self.has_flag(ReviewFlag.SUGGEST_REMOVAL)

    def is_approved(self):
        return self.has_flag(ReviewFlag.MODERATOR_APPROVAL)

    def has_flag(self, flag_name):
        # assume that self.flags.all() has been pre-fetched
        for flag in self.flags.all():
            if flag.flag == flag_name:
                return True
        return False


    @property
    def anchor(self):
        return "review%d" % self.id

    def as_text(self):
        """
        Returns a text version of this review suitable for inclusion in an email.
        """
        text = self.__unicode__()
        if self.id:
            text += "\n" + get_full_url(self)
        return text

    def __unicode__(self):
        return """
        name:    %s
        rating:  %d
        summary: %s

        %s
        """ % (self.user.public_name() or "anonymous user",
               self.rating,
               self.summary,
               self.review or "(reviewer did not provide details)")

    def clean(self):
        super(Review, self).clean()
        if Review.objects.filter(user=self.user, product=self.product).exclude(id=self.id).exists():
            raise ValidationError("The user cannot review the same product more than once")
        if not self.user.public_name():
            raise ValidationError("The associated user does not have a public profile.")

    def get_spam_data(self, request=None):
        data = super(Review, self).get_spam_data(request)
        review_content = self.summary
        if self.review:
            review_content += "\n" + self.review
        data.update({
            'comment_type': 'review',
            'comment_author': self.user.public_name() or self.user.username or '',
            'comment_author_email': self.user.email or '',
            'comment_content': review_content,
        })
        return data


class ReviewFlag(models.Model):
    """
    Records a flag on a review. This is intentionally flexible; right now, a
    flag could be:

        * A "removal suggestion" -- where a user suggests a review for (potential) removal.

        * A "moderator approval" -- used when a moderator approves a review after it's been flagged for removal

    You can (ab)use this model to add other flags, if needed. However, by
    design users are only allowed to flag a review with a given flag once.
    """
    user      = models.ForeignKey(User, related_name="review_flags")
    review   = models.ForeignKey(Review, related_name="flags")
    flag      = models.CharField(max_length=30, db_index=True)
    flag_date = models.DateTimeField(auto_now_add=True)

    # Constants for flag types
    SUGGEST_REMOVAL = "removal suggestion"
    MODERATOR_APPROVAL = "moderator approval"

    class Meta:
        unique_together = [('user', 'review', 'flag')]

    def __unicode__(self):
        return "%s flag of review ID %s by %s" % \
               (self.flag, self.review_id, self.user.username)