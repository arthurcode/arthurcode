from django.db import models
from utils.validators import not_blank
from datetime import date


class Discount(models.Model):

    CODE_MAX_LENGTH = 20
    NAME_MAX_LENGTH = 50

    # discount types
    FIXED = 1         # customer saves a fixed dollar amount
    VARIABLE = 2      # discount cannot be computed ahead of time
    PERCENTAGE = 3    # discount is a percentage
    TYPES = ((FIXED, 'Fixed'),
             (VARIABLE, 'Variable'),
             (PERCENTAGE, 'Percentage'))

    # redemption scheme
    PROMOTION = 1  # can be used an unlimited number of times during the valid period
    COUPON = 2     # can only be used once
    REDEMPTION_SCHEME_CHOICES = ((PROMOTION, 'Promotion'),
                                 (COUPON, 'Coupon'))

    # applies to
    ITEM = 1
    MERCHANDISE_SUBTOTAL = 2
    SHIPPING = 3
    APPLIES_TO_CHOICES = ((ITEM, 'Item'),
                          (MERCHANDISE_SUBTOTAL, 'Subtotal'),
                          (SHIPPING, 'Shipping'))

    code = models.CharField(max_length=CODE_MAX_LENGTH, validators=[not_blank], unique=True)
    name = models.CharField(max_length=NAME_MAX_LENGTH, validators=[not_blank])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    type = models.SmallIntegerField(choices=TYPES)
    amount = models.PositiveIntegerField(null=True, blank=True, help_text='The discount amount as a dollar value or a percentage. Can be left blank for variable discounts.')
    redemption_scheme = models.SmallIntegerField(choices=REDEMPTION_SCHEME_CHOICES)
    applies_to = models.SmallIntegerField(choices=APPLIES_TO_CHOICES)

    @property
    def is_active(self):
        return not self.is_expired

    @property
    def is_expired(self):
        today = date.today()
        return today < self.start_date or (self.end_date is not None and today > self.end_date)
