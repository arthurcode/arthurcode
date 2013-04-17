from django import forms
from catalogue.models import Product
from cart.models import CartItem


class ProductAddToCartForm(forms.Form):
    ERROR_COOKIES_DISABLED = u"Your browser must have cookies enabled in order to shop on this site."


    quantity = forms.IntegerField(widget=forms.TextInput(attrs={'size': '2',
                                                                'value': '1',
                                                                'class': 'quantity',
                                                                'maxlength': '5'}),
                                  error_messages={'invalid': 'Please enter a valid quantity.'},
                                  min_value=1)
    product_slug = forms.CharField(widget=forms.HiddenInput())

    # override the default __init__ so we can set the request
    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super(ProductAddToCartForm, self).__init__(*args, **kwargs)

    # custom validation to check for cookies
    def clean(self):
        cleaned_data = super(ProductAddToCartForm, self).clean()
        product_slug = cleaned_data.get('product_slug', None)
        quantity = cleaned_data.get('quantity', None)

        if product_slug and quantity:
            product = Product.objects.get(slug=product_slug)
            if product and product.quantity < quantity:
                msg = ProductAddToCartForm.get_insufficient_stock_msg(product.quantity)
                self._errors['quantity'] = self.error_class([msg])
                del(cleaned_data['quantity'])

        if self.request:
            if not self.request.session.test_cookie_worked():
                # even though this is a general form error, associate it with the quantity field.  This makes displaying
                # the error message a little more automatic.
                self._errors['quantity'] = self.error_class([ProductAddToCartForm.ERROR_COOKIES_DISABLED])
                if 'quantity' in cleaned_data:
                    del(cleaned_data['quantity'])
        return cleaned_data

    @classmethod
    def get_insufficient_stock_msg(cls, in_stock):
        if in_stock <= 0:
            return u"Sorry, this product is now out of stock."
        elif in_stock == 1:
            return u"Sorry, there is only 1 left in stock."
        else:
            return u"Sorry, there are only %d left in stock." % in_stock


class UpdateCartItemForm(forms.Form):
    quantity = forms.IntegerField(widget=forms.TextInput(attrs={'size': '2',
                                                                'class': 'quantity',
                                                                'maxlength': '5'}),
                                  error_messages={'invalid': 'Please enter a valid quantity.'},
                                  min_value=0)
    item_id = forms.IntegerField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super(UpdateCartItemForm, self).clean()
        quantity = cleaned_data.get('quantity', None)
        item_id = cleaned_data.get('item_id', None)

        if quantity and item_id:
            item = CartItem.objects.get(id=item_id)
            if item:
                in_stock = item.product.quantity
                if quantity > in_stock:
                    msg = ProductAddToCartForm.get_insufficient_stock_msg(in_stock)
                    self._errors['quantity'] = self.error_class([msg])
                    del(cleaned_data['quantity'])
        return cleaned_data

