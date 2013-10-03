from django import forms
from accounts.forms import DEFAULT_EMAIL_WIDGET
from catalogue.models import ProductInstance, RestockNotification
from django.core.exceptions import ValidationError
from cart.forms import ProductAddToCartForm
from wishlists.models import WishList


class RestockNotifyForm(forms.Form):
    email = forms.EmailField(widget=DEFAULT_EMAIL_WIDGET)
    instance_id = forms.IntegerField(widget=forms.HiddenInput)

    def clean(self):
        cd = super(RestockNotifyForm, self).clean()
        instance = self._get_product_instance(cd)

        if instance:
            if instance.quantity > 0:
                raise ValidationError('This product is currently in stock.')
        else:
            raise ValidationError('We could not find the specified product.')
        return cd

    def save(self):
        """
        Create a restock notification for this product instance and email combination.  If a notification already
        exists then do nothing and return success.
        """
        instance_id = self.cleaned_data.get('instance_id', None)
        email = self.cleaned_data.get('email', None)
        existing_notifications = RestockNotification.objects.filter(instance__id=instance_id, email=email)

        if existing_notifications.exists():
            return

        product_instance = self._get_product_instance(self.cleaned_data)
        notification = RestockNotification(instance=product_instance, email=email)
        notification.full_clean()
        notification.save()

    def _get_product_instance(self, cleaned_data):
        instance_id = cleaned_data.get('instance_id', None)
        if instance_id:
            instances = ProductInstance.objects.filter(id=instance_id)
            if instances.exists():
                return instances[0]
        return None


class AddToWishListForm(ProductAddToCartForm):
    """
    A form that says "Hi, I would like to add this product instance to 'a' wishlist".  The customer will choose which
    wishlist they would like to add it to at the end of the process.
    """

    def check_stock(self, cleaned_data):
        """
        We can add out-of-stock items to a wish list, so disable this check in the clean routine.
        """
        return cleaned_data


    def save(self):
        # this method can't save the product to the wishlist, because we don't know which wishlist to add it to.
        return None
