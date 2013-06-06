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

    CONTACT_METHOD = ((EMAIL, 'Email'),
                      (PHONE, 'Phone'))

    user = models.OneToOneField(User, related_name="customer_profile")
    phone = models.CharField(max_length=AbstractAddress.PHONE_NUMBER_LENGTH, null=True, blank=True)
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

    def humanized_contact_method(self):
        """
        Return the human-readable contact-method string.
        """
        for method in CustomerProfile.CONTACT_METHOD:
            if method[0] == self.contact_method:
                return method[1]
        return "Unknown"


class CustomerShippingAddress(AbstractAddress):
    # a customer can have several shipping addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile, related_name='shipping_addresses')
    last_used = models.DateTimeField(auto_now_add=True)


class CustomerBillingAddress(AbstractAddress):
    # a customer can have several billing addresses associated with their profile
    customer = models.ForeignKey(CustomerProfile, related_name='billing_addresses')
    last_used = models.DateTimeField(auto_now_add=True)


# add a new method to the builtin User class
def patch_user(user_clazz):
    def public_name(self):
        try:
            return self.public_profile.username
        except PublicProfile.DoesNotExist:
            return None
    user_clazz.public_name = public_name

# add custom methods to the built-in User class
patch_user(User)

