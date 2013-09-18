from django import forms
from accounts.forms import DEFAULT_EMAIL_WIDGET
from catalogue.models import ProductInstance
from django.core.exceptions import ValidationError


class RestockNotifyForm(forms.Form):
    email = forms.EmailField(widget=DEFAULT_EMAIL_WIDGET)
    instance_id = forms.IntegerField(widget=forms.HiddenInput)

    def clean(self):
        cd = super(RestockNotifyForm, self).clean()
        instance_id = cd.get('instance_id', None)

        if instance_id:
            instances = ProductInstance.objects.filter(id=instance_id)
            if instances.exists():
                instance = instances[0]
                if instance.quantity > 0:
                    raise ValidationError('This product is currently in stock.')
            else:
                raise ValidationError('We could not find the specified product.')
        return cd

    def save(self):
        pass


