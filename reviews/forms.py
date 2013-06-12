from django import forms
from django.core.exceptions import ValidationError

from reviews.models import Review
from utils.validators import not_blank
import arthurcode.settings as settings
from reviews.signals import review_edited


class ReviewForm(forms.Form):
    rating = forms.ChoiceField(choices=Review.RATING_CHOICES, label="Your Rating")
    summary = forms.CharField(max_length=Review.SUMMARY_LENGTH, validators=[not_blank],
                              help_text="summarize your review in %d characters or less" % Review.SUMMARY_LENGTH)
    review = forms.CharField(widget=forms.Textarea, label="Detailed Review", required=False)

    def __init__(self, request, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        super(ReviewForm, self).clean()
        if not self.request.user.is_authenticated:
            raise ValidationError(u"Sorry, you must login before you are allowed to review products.")
        if not getattr(settings, 'ALLOW_REVIEWS', True):
            raise ValidationError(u"Reviews are temporarily disabled.  Sorry for the inconvenience.")


class AddReviewForm(ReviewForm):

    def __init__(self, request, product, *args, **kwargs):
        super(AddReviewForm, self).__init__(request, *args, **kwargs)
        self.product = product

    def clean(self):
        super(AddReviewForm, self).clean()
        if Review.objects.filter(user=self.request.user, product=self.product).exists():
            raise ValidationError(u"You have already reviewed this product. "
                                  u"Please edit or delete your original review.")

    def create_review(self, commit=True):
        review = Review(product=self.product)
        review.rating = self.data['rating']
        review.summary = self.data['summary']
        review.review = self.data['review']
        review.user = self.request.user
        if commit:
            review.full_clean()
            review.save()
        return review


class EditReviewForm(ReviewForm):

    def __init__(self, request, review, *args, **kwargs):
        initial = {
            'rating': review.rating,
            'summary': review.summary,
            'review': review.review
        }
        kwargs['initial'] = initial
        super(EditReviewForm, self).__init__(request, *args, **kwargs)
        self.review = review
        self.original_review = self.review.as_text()

    def clean(self):
        super(EditReviewForm, self).clean()
        if not self.review.user == self.request.user:
            raise ValidationError("This review was created under a different account and cannot be edited.")

    def edit_review(self, commit=True):
        self.review.rating = self.data['rating']
        self.review.summary = self.data['summary']
        self.review.review = self.data['review']
        if commit:
            self.review.full_clean()
            self.review.save()
            review_edited.send(sender=self.review, original=self.original_review)
        return self.review