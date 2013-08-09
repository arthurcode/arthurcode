from django import forms
from cart.models import CartItem
import cartutils
from django.core.exceptions import ValidationError


class ProductAddToCartForm(forms.Form):
    ERROR_COOKIES_DISABLED = u"Your browser must have cookies enabled in order to shop on this site."


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

        if self.product.has_options():
            # TODO: add option fields to the form
            pass

    # custom validation to check for cookies
    def clean(self):
        cleaned_data = super(ProductAddToCartForm, self).clean()
        quantity = cleaned_data.get('quantity', None)

        if self.request:
            if not self.request.session.test_cookie_worked():
                # even though this is a general form error, associate it with the quantity field.  This makes displaying
                # the error message a little more automatic.
                self._errors['quantity'] = self.error_class([ProductAddToCartForm.ERROR_COOKIES_DISABLED])
                if 'quantity' in cleaned_data:
                    del(cleaned_data['quantity'])
            elif quantity:
                instance = self.get_product_instance(cleaned_data)
                error = check_stock(instance, self.request, quantity_to_add=quantity)
                if error:
                    self._errors['quantity'] = self.error_class([error])
                    del(cleaned_data['quantity'])
        return cleaned_data

    def get_product_instance(self, cleaned_data):
        """
        Gets the product instance from the product itself together with the options the user has chosen
        """
        return self.product.instances.all()[0]  #TODO fix me

    def save(self):
        """
        Adds the product instance to the customer's cart
        """
        instance = self.get_product_instance(self.cleaned_data)
        cartutils.add_to_cart(self.request, instance, self.cleaned_data.get('quantity', 0))


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
            item = CartItem.objects.get(id=item_id)
            if item:
                error = check_stock(item.item, self.request, final_quantity=quantity)
                if error:
                    self._errors['quantity'] = self.error_class([error])
                    del(cleaned_data['quantity'])
        return cleaned_data


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


