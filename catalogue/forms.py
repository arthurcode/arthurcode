from django import forms
from accounts.forms import DEFAULT_EMAIL_WIDGET
from catalogue.models import ProductInstance, RestockNotification
from django.core.exceptions import ValidationError


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



