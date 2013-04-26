from django.db import models
from django.contrib.auth.models import User
from utils.models import AbstractAddress
from utils.validators import is_blank
from django.core.exceptions import ValidationError


class CustomerProfile(models.Model):
    """
    Collects customer-specific information, such as shipping and billing addresses and phone numbers.
    A user can only have one customer profile.
    """
    PHONE = 1
    EMAIL = 2

    CONTACT_METHOD = ((EMAIL, 'Email'),
                      (PHONE, 'Phone'))

    user = models.ForeignKey(User, unique=True)
    phone_number = models.CharField(max_length=AbstractAddress.PHONE_NUMBER_LENGTH, null=True, blank=True)
    date_added = models.DateField(auto_now_add=True)
    contact_method = models.SmallIntegerField(choices=CONTACT_METHOD, default=EMAIL)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    def __unicode__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, self.user.username)

    def clean(self):
        # verify that the user model has a non-null first and last name field
        if self.user_id and (is_blank(self.user.first_name) or is_blank(self.user.last_name)):
            raise ValidationError(u"The associated user's first and/or last name cannot be blank")


class CustomerShippingAddress(AbstractAddress):
    # a customer can have several shipping addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile)
    last_used = models.DateTimeField(auto_now_add=True)


class CustomerBillingAddress(AbstractAddress):
    # a customer can have several billing addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile)
    last_used = models.DateTimeField(auto_now_add=True)

