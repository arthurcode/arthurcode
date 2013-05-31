from django import forms
from catalogue.models import Review, Product
from utils.validators import not_blank
from django.core.exceptions import ValidationError


class ReviewForm(forms.Form):

    name = forms.CharField(max_length=Review.NAME_LENGTH, validators=[not_blank], label="Your Name",
                           help_text="as you want it to appear on the public review")
    rating = forms.ChoiceField(choices=Review.RATING_CHOICES, label="Your Rating")
    title = forms.CharField(max_length=Review.TITLE_LENGTH, validators=[not_blank],
                            help_text="summarize your review in %d characters or less" % Review.TITLE_LENGTH)
    review = forms.CharField(widget=forms.Textarea, label="Full Review")
    product = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.request = request
        if self.request.user.first_name:
            self.fields['name'].initial = self.request.user.first_name

    def clean(self):
        if not self.request.user.is_authenticated:
            raise ValidationError(u"Sorry, you must login before you are allowed to review products.")
        if not Product.objects.filter(id=self.cleaned_data['product']).exists():
            raise ValidationError(u"Unable to find the product linked to this review.")

    def create_review(self, commit=True):
        product = Product.objects.get(id=self.data['product'])
        review = Review(product=product)
        review.name = self.data['name']
        review.rating = self.data['rating']
        review.title = self.data['title']
        review.review = self.data['review']
        review.user = self.request.user
        if commit:
            review.save()
        return review


