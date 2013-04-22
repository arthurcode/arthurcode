from django.db import models
from django.contrib.auth.models import User
from utils.models import AbstractAddress


class CustomerProfile(models.Model):
    """
    Collects customer-specific information, such as shipping and billing addresses and phone numbers.
    A user can only have one customer profile.
    """
    user = models.ForeignKey(User, unique=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)


class CustomerShippingAddress(AbstractAddress):
    # a customer can have several shipping addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile)


class CustomerBillingAddress(AbstractAddress):
    # a customer can have several billing addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile)

