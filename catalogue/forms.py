from django import forms
from catalogue.models import Review
from utils.validators import not_blank
from django.core.exceptions import ValidationError


class AddReviewForm(forms.Form):

    name = forms.CharField(max_length=Review.NAME_LENGTH, validators=[not_blank], label="Your Name",
                           help_text="as you want it to appear on the public review")
    rating = forms.ChoiceField(choices=Review.RATING_CHOICES, label="Your Rating")
    summary = forms.CharField(max_length=Review.SUMMARY_LENGTH, validators=[not_blank],
                            help_text="summarize your review in %d characters or less" % Review.SUMMARY_LENGTH)
    review = forms.CharField(widget=forms.Textarea, label="Detailed Review", required=False)

    def __init__(self, request, *args, **kwargs):
        super(AddReviewForm, self).__init__(*args, **kwargs)
        self.request = request
        if self.request.user.first_name:
            self.fields['name'].initial = self.request.user.first_name

    def clean(self):
        if not self.request.user.is_authenticated:
            raise ValidationError(u"Sorry, you must login before you are allowed to review products.")

    def create_review(self, product, commit=True):
        review = Review(product=product)
        review.name = self.data['name']
        review.rating = self.data['rating']
        review.summary = self.data['summary']
        review.review = self.data['review']
        review.user = self.request.user
        if commit:
            review.save()
        return review


