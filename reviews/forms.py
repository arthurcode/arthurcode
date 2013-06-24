from django import forms
from django.core.exceptions import ValidationError
from reviews.models import Review, ReviewFlag
from utils.validators import not_blank
import arthurcode.settings as settings
from reviews.signals import review_edited
from reviews.email import notify_managers_review_deleted_by_admin, notify_author_review_deleted_by_admin

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
        review = self.create_review(commit=False)
        if review.check_spam(self.request):
            raise ValidationError("This review has been flagged as spam and will not be accepted.")

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
        review = self.edit_review(commit=False)
        if review.check_spam(self.request):
            raise ValidationError("This review edit has been marked as spam and will not be accepted.")

    def edit_review(self, commit=True):
        self.review.rating = self.data['rating']
        self.review.summary = self.data['summary']
        self.review.review = self.data['review']
        if commit:
            self.review.full_clean()
            self.review.save()
            review_edited.send(sender=self.review, original=self.original_review)
        return self.review


class FlagReviewForm(forms.Form):

    def __init__(self, request, review, *args, **kwargs):
        super(FlagReviewForm, self).__init__(*args, **kwargs)
        self.request = request
        self.review = review

    def clean(self):
        if not self.request.user.is_authenticated:
            raise ValidationError("Sorry, you must be logged in to flag reviews.")  # shouldn't happen
        if self.review.is_approved():
            raise ValidationError("This review has already been reviewed and approved by a staff member.")
        if self.review.is_flagged_for_removal():
            raise ValidationError("This review has already been flagged for removal.")
        if ReviewFlag.objects.filter(user=self.request.user, review=self.review, flag=ReviewFlag.SUGGEST_REMOVAL).exists():
            raise ValidationError("Sorry, you have already flagged this review for removal.")

    def do_flag(self):
        flag = ReviewFlag(user=self.request.user, review=self.review, flag=ReviewFlag.SUGGEST_REMOVAL)
        flag.full_clean()
        flag.save()


class AdminDeleteReviewForm(forms.Form):

    email_author = forms.BooleanField(label="Send Email to Author?", initial=True, required=False)
    reason = forms.CharField(max_length=1000, widget=forms.Textarea, validators=[not_blank])

    def __init__(self, request, review, *args, **kwargs):
        super(AdminDeleteReviewForm, self).__init__(*args, **kwargs)
        self.request = request
        self.review = review

    def clean(self):
        super(AdminDeleteReviewForm, self).clean()
        if not self.request.user.is_staff:
            raise ValidationError("Only staff members are allowed to delete reviews.")

        email_author = self.cleaned_data.get('email_author', False)

        if email_author:
            if not self.review.user.email:
                raise ValidationError("The reviewer does not have an email address on file.  "
                                          "Please un-check the 'Email Author' box.")
        return self.cleaned_data

    def delete_review(self):
        email_author = self.cleaned_data.get('email_author', False)
        reason = self.cleaned_data.get('reason', '(reason not provided)')
        self.review.delete()

        if email_author:
            notify_author_review_deleted_by_admin(self.request, self.review, reason)
        notify_managers_review_deleted_by_admin(self.request, self.review, reason)


