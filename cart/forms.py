from django import forms
from catalogue.models import ProductInstance
from cart.models import CartItem, GiftCardCartItem
import cartutils
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from wishlists.models import WishList
from accounts.accountutils import is_regular_user
from cart.models import ProductCartItem
from giftcards.forms import DEFAULT_GC_VALUE_WIDGET


class ProductAddToCartForm(forms.Form):
    ERROR_COOKIES_DISABLED = u"Your browser must have cookies enabled in order to shop on this site."
    ERROR_OUT_OF_STOCK = u"Sorry, this product is out of stock."
    ERROR_UNAVAILABLE = u"Sorry, this product is unavailable."
    NEW_WISHLIST_ID = -1


    quantity = forms.IntegerField(widget=forms.TextInput(attrs={'size': '2',
                                                                'value': '1',
                                                                'class': 'quantity',
                                                                'maxlength': '5'}),
                                  error_messages={'invalid': 'Please enter a valid quantity.'},
                                  min_value=1)

    def __init__(self, product, request=None, *args, **kwargs):
        self.product = product
        self.request = request
        super(ProductAddToCartForm, self).__init__(*args, **kwargs)
        self.extra_fields = []

        if self.product.has_options():
            opt_map = self.product.get_options()
            for category, options in opt_map.items():
                choices = [(o.id, o.name) for o in options]
                required_error = u"You must choose a %s" % category.lower()
                self.fields[category] = forms.ChoiceField(choices=choices,
                                                          label="Select a %s:" % category.capitalize(), widget=forms.RadioSelect,
                                                          required=True,
                                                          error_messages={'required': required_error})
                self.extra_fields.append(category)

        if is_regular_user(self.request.user):
            wishlists = WishList.objects.filter(user=request.user)
            choices = [(w.id, w.name) for w in wishlists]
            choices.append((self.NEW_WISHLIST_ID, 'New Wish List'))
            self.fields['wishlist'] = forms.ChoiceField(choices=choices)

    # custom validation to check for cookies
    def clean(self):
        cleaned_data = super(ProductAddToCartForm, self).clean()
        all_extra_fields_set = True
        for field in self.extra_fields:
            if cleaned_data.get(field) is None:
                all_extra_fields_set = False
                break

        if self.request:
            if not self.request.session.test_cookie_worked():
                # even though this is a general form error, associate it with the quantity field.  This makes displaying
                # the error message a little more automatic.
                self._errors['quantity'] = self.error_class([ProductAddToCartForm.ERROR_COOKIES_DISABLED])
                if 'quantity' in cleaned_data:
                    del(cleaned_data['quantity'])
            elif all_extra_fields_set:
                wishlist_id = self.cleaned_data.get('wishlist', None)
                self.check_available(cleaned_data)

                if not "add-to-wishlist" in self.request.POST:
                    # the stock not relevant if we are just adding the item to a wish list
                    self.check_stock(cleaned_data)
        return cleaned_data

    def get_product_instance(self, cleaned_data):
        """
        Gets the product instance from the product itself together with the options the user has chosen.  Returns None
        if a product instance does not exist with this particular set of options.  Raises a validation error if more
        than one product-instance matches this option set.
        """

        options = [cleaned_data.get(f) for f in self.extra_fields]
        instances = ProductInstance.objects.filter(product=self.product)

        for option_id in options:
            products = ProductInstance.objects.filter(options__id=option_id)
            instances = instances.filter(pk__in=products)  # set intersection

        if instances.count() > 1:
            raise ValidationError("Internal Error: there was more than one product with this option set.")
        if instances.count() == 0:
            return None
        return instances[0]

    def check_available(self, cleaned_data):
        instance = self.get_product_instance(cleaned_data)
        if not instance:
            raise ValidationError(self.ERROR_UNAVAILABLE)

    def check_stock(self, cleaned_data):
        quantity = cleaned_data.get('quantity', 0)
        instance = self.get_product_instance(cleaned_data)
        if instance and quantity:
            if instance.quantity <= 0:
                # if the product is completely out of stock make this a general error
                url = reverse("restock_notify", args=[instance.id])
                error = self.ERROR_OUT_OF_STOCK + \
                        " <a class='standard' href='%s'>Email me when it becomes available.</a>" % url
                raise ValidationError(error)

            error = check_stock(instance, self.request, quantity_to_add=quantity)
            if error:
                self._errors['quantity'] = self.error_class([error])
                del(cleaned_data['quantity'])


    def add_to_cart(self):
        instance = self.get_product_instance(self.cleaned_data)
        cartutils.add_to_cart(self.request, instance, self.cleaned_data.get('quantity', 0))

    def add_to_wishlist(self):
        product_instance = self.get_product_instance(self.cleaned_data)
        wishlist_id = self.cleaned_data.get('wishlist', None)
        if wishlist_id is None or wishlist_id == self.NEW_WISHLIST_ID:
            # this method doesn't apply
            return None
        try:
            wishlist = WishList.objects.get(id=wishlist_id)
            wishlist.add_product(product_instance)
            return wishlist
        except WishList.DoesNotExist:
            return None


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(widget=forms.TextInput(attrs={'size': '2',
                                                                'class': 'quantity',
                                                                'maxlength': '5'}),
                                  error_messages={'invalid': 'Please enter a valid quantity.'},
                                  min_value=0)
    item_id = forms.IntegerField(widget=forms.HiddenInput())

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super(UpdateCartItemForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UpdateCartItemForm, self).clean()
        quantity = cleaned_data.get('quantity', None)
        item_id = cleaned_data.get('item_id', None)

        if quantity and item_id:
            item = cartutils.get_base_item(item_id)
            if item and isinstance(item, ProductCartItem):
                error = check_stock(item.item, self.request, final_quantity=quantity)
                if error:
                    self._errors['quantity'] = self.error_class([error])
                    del(cleaned_data['quantity'])
        return cleaned_data


class AddGiftCardToCartForm(forms.Form):
    value = forms.IntegerField(min_value=GiftCardCartItem.MIN_VALUE, max_value=GiftCardCartItem.MAX_VALUE,
                               help_text="Any amount between $%d and $%d" % (GiftCardCartItem.MIN_VALUE, GiftCardCartItem.MAX_VALUE),
                               widget=DEFAULT_GC_VALUE_WIDGET, label="Amount $")

    def save(self, request):
        value = self.cleaned_data.get('value')
        cartutils.add_gift_card_to_cart(request, value, 1)


def check_stock(item, request, final_quantity=None, quantity_to_add=0):
    """
    Check whether there is enough product to satisfy the given cart request.  From the request we can get the
    current number of products in their cart.  If final_quantity != None then the customer is using the update_cart
    form to modify their cart.  If quantity_to_add > 0 then they are using the add-to-cart form to modify their cart.
    A different error message is displayed in each case.

    Returns None if the request is valid.  Returns an error message if the request is invalid.
    """
    in_stock = item.quantity
    in_cart = 0
    cart_item = cartutils.get_item_for_product(request, item)
    if cart_item:
        in_cart = cart_item.quantity

    if final_quantity:
        if final_quantity > in_stock:
            return CartItem.get_insufficient_stock_msg(in_stock)
    elif quantity_to_add > 0:
        total = quantity_to_add + in_cart
        if total > in_stock:
            msg = CartItem.get_insufficient_stock_msg(in_stock)
            if in_cart > 0:
                msg += " You already have %d in your cart." % in_cart
            return msg
    return None


