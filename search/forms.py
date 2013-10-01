from django import forms
from search.models import SearchTerm
from utils.validators import not_blank
from django.core.validators import ValidationError


class SearchForm(forms.Form):
    q = forms.CharField(max_length=SearchTerm.TERM_LENGTH, min_length=3, validators=[not_blank])
    category_slug = forms.CharField(max_length=50, required=False)

    def clean_q(self):
        text = self.cleaned_data.get('q', None)
        if text:
            text = text.strip()
            if len(text) < 3:
                raise ValidationError("Search text must contain at least 3 characters")
        return text
