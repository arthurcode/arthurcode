from django import forms
from catalogue.models import Review, Product
from utils.validators import not_blank
from django.core.exceptions import ValidationError


class ReviewForm(forms.Form):

    rating = forms.ChoiceField(choices=Review.RATING_CHOICES, label="Your Rating")
    title = forms.CharField(max_length=Review.TITLE_LENGTH, validators=[not_blank],
                            help_text="summarize your review in %d characters or less" % Review.TITLE_LENGTH)
    review = forms.CharField(widget=forms.Textarea, label="Full Review")
    product = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        if not self.request.user.is_authenticated:
            raise ValidationError(u"Sorry, you must login before you are allowed to review products.")
        if not Product.objects.filter(id=self.cleaned_data['product']).exists():
            raise ValidationError(u"Unable to find the product linked to this review.")

    def create_review(self, commit=True):
        product = Product.objects.get(id=self.data['product'])
        review = Review(product=product)
        review.rating = self.data['rating']
        review.title = self.data['title']
        review.review = self.data['review']
        review.user = self.request.user
        if commit:
            review.save()
        return review


