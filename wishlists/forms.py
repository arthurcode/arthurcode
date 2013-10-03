from django import forms
from models import WishList
from accounts.accountutils import is_regular_user
from django.core.exceptions import ValidationError
from utils.validators import not_blank

DEFAULT_NAME_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength': WishList.NAME_MAX_LENGTH})
DEFAULT_DESCRIPTION_WIDGET = forms.Textarea(attrs={'maxlength': WishList.DESCRIPTION_MAX_LENGTH, 'cols': 40, 'rows': 4})

class CreateWishListForm(forms.Form):

    name = forms.CharField(max_length=WishList.NAME_MAX_LENGTH, help_text="Example: Brody's 9th Birthday",
                           validators=[not_blank], widget=DEFAULT_NAME_WIDGET)
    description = forms.CharField(max_length=WishList.DESCRIPTION_MAX_LENGTH, required=False,
                                  widget=DEFAULT_DESCRIPTION_WIDGET,
                                  help_text="Extra (optional) information for friends and family members who will "
                                            "be using this list")

    def __init__(self, request, *args, **kwargs):
        super(CreateWishListForm, self).__init__(*args, **kwargs)
        self.request = request

    def clean_name(self):
        name = self.cleaned_data.get('name', None)
        if name:
            if WishList.objects.filter(user=self.request.user, name=name).exists():
                raise ValidationError("You already have a wish list with this name.")
        return name

    def clean(self):
        if not is_regular_user(self.request.user):
            raise ValidationError("Sorry, only logged-in users can create wishlists.")
        return super(CreateWishListForm, self).clean()

    def save(self):
        name = self.cleaned_data.get('name')
        description = self.cleaned_data.get('description', None)
        wishlist = WishList(user=self.request.user, name=name, description=description)
        wishlist.full_clean()
        wishlist.save()
        return wishlist


