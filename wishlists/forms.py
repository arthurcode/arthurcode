from django import forms
from models import WishList, WishListItem
from accounts.accountutils import is_regular_user
from django.core.exceptions import ValidationError
from utils.validators import not_blank
from catalogue.models import ProductInstance
from cart.cartutils import add_to_cart

DEFAULT_NAME_WIDGET = forms.TextInput(attrs={'size': 40, 'maxlength': WishList.NAME_MAX_LENGTH})
DEFAULT_DESCRIPTION_WIDGET = forms.Textarea(attrs={'maxlength': WishList.DESCRIPTION_MAX_LENGTH, 'cols': 40, 'rows': 4})


class CreateWishListForm(forms.Form):

    name = forms.CharField(max_length=WishList.NAME_MAX_LENGTH, help_text="Example: Brody's 9th Birthday",
                           validators=[not_blank], widget=DEFAULT_NAME_WIDGET)
    description = forms.CharField(max_length=WishList.DESCRIPTION_MAX_LENGTH, required=False,
                                  widget=DEFAULT_DESCRIPTION_WIDGET,
                                  help_text="Extra (optional) information for friends and family members who will "
                                            "be using this list")

    # holds the id of the product instance we should add to this wish list after it is created, if any
    instance_id = forms.IntegerField(widget=forms.HiddenInput, required=False)

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
        instance_id = self.cleaned_data.get('instance_id', None)

        wishlist = WishList(user=self.request.user, name=name, description=description)
        wishlist.full_clean()
        wishlist.save()
        if instance_id:
            try:
                product_instance = ProductInstance.objects.get(id=instance_id)
                wishlist.add_product(product_instance)
            except ProductInstance.DoesNotExist:
                pass

        return wishlist


class RemoveFromWishList(forms.Form):

    instance_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(RemoveFromWishList, self).__init__(*args, **kwargs)
        self.request = request

    def clean(self):
        cd = super(RemoveFromWishList, self).clean()
        instance_id = cd.get('instance_id', None)
        if instance_id:
            item = WishListItem.objects.get(id=instance_id)
            if self.request.user != item.wish_list.user:
                return ValidationError(u"You do not have permission to delete this wish list item.")
        return cd

    def save(self):
        # TODO: under certain conditions we may not want to allow the user to delete items from their lists
        instance_id = self.cleaned_data.get('instance_id')
        item = WishListItem.objects.get(id=instance_id)
        item.delete()


class AddWishListItemToCart(forms.Form):

    instance_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, request, *args, **kwargs):
        super(AddWishListItemToCart, self).__init__(*args, **kwargs)
        self.request = request

    def save(self):
        instance_id = self.cleaned_data.get('instance_id')
        instance = ProductInstance.objects.get(id=instance_id)
        add_to_cart(self.request, instance, 1)