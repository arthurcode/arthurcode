from django.db import models
from django.contrib.auth.models import User
from utils.models import AbstractAddress
from utils.validators import is_blank, not_blank
from django.core.exceptions import ValidationError


class PublicProfile(models.Model):
    """
    Collects aspects of a user's public profile.  This is the information that will be displayed when the user
    places a product review, or comments on a blog post or product review.  Most of this information is optional.
    The only thing required is the name (public handle).
    """
    NAME_LENGTH = 50
    DESCRIPTION_LENGTH = 100
    LOCATION_LENGTH = 100

    user = models.OneToOneField(User, related_name="public_profile")
    username = models.CharField(max_length=NAME_LENGTH, validators=[not_blank])
    description = models.CharField(max_length=DESCRIPTION_LENGTH, null=True, blank=True)
    location = models.CharField(max_length=LOCATION_LENGTH, null=True, blank=True)


class CustomerProfile(models.Model):
    """
    Collects customer-specific information, such as shipping and billing addresses and phone numbers.
    A user can only have one customer profile.
    """
    PHONE = 1
    EMAIL = 2
    UNKNOWN = 3

    CONTACT_METHOD = ((EMAIL, 'Email'),
                      (PHONE, 'Phone'),
                      (UNKNOWN, 'Unknown'))

    user = models.OneToOneField(User, related_name="customer_profile")
    phone = models.CharField(max_length=AbstractAddress.PHONE_NUMBER_LENGTH, null=True, blank=True)
    date_added = models.DateField(auto_now_add=True)
    contact_method = models.SmallIntegerField(choices=CONTACT_METHOD, default=UNKNOWN)
    on_mailing_list = models.BooleanField(default=False)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    def __unicode__(self):
        return "customer profile for user %s (%s)" % (self.user.username, self.user.email or "email unknown")


class CustomerShippingAddress(AbstractAddress):

    NICKNAME_MAX_LENGTH = 50

    # a customer can have several shipping addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile, related_name='shipping_addresses')
    last_used = models.DateTimeField(auto_now_add=True)
    nickname = models.CharField(max_length=NICKNAME_MAX_LENGTH)


class CustomerBillingAddress(AbstractAddress):
    # a customer can have several billing addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile, related_name='billing_addresses')
    last_used = models.DateTimeField(auto_now_add=True)


# add a new method to the builtin User class
def patch_user(user_clazz):
    def public_name(self):
        profile = self.get_public_profile()
        if profile:
            return profile.username
        return None

    def get_public_profile(self):
        try:
            return self.public_profile
        except PublicProfile.DoesNotExist:
            return None

    def get_customer_profile(self):
        try:
            return self.customer_profile
        except CustomerProfile.DoesNotExist:
            return None

    user_clazz.public_name = public_name
    user_clazz.get_public_profile = get_public_profile
    user_clazz.get_customer_profile = get_customer_profile

# add custom methods to the built-in User class
patch_user(User)

