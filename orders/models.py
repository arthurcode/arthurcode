from django.db import models
from django.db.transaction import commit_on_success
from catalogue.models import ProductInstance
from django.core.validators import MinValueValidator
from accounts.models import CustomerProfile
from utils.models import AbstractAddress
from utils.validators import is_blank, not_blank
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from decimal import Decimal
from orders.signals import signal_order_cancelled
from django.contrib.auth.models import User


class Order(models.Model):
    """
    Represents a customer's order.
    """

    SUBMITTED = 1
    PROCESSED = 2
    SHIPPED = 3
    CANCELLED = 4

    ORDER_STATUSES = ((SUBMITTED, 'Submitted'),
                      (PROCESSED, 'Processed'),
                      (SHIPPED, 'Shipped'),
                      (CANCELLED, 'Cancelled'))

    # will be null if the customer checks out as a guest, or if the order is done in-person or over the phone.
    user = models.ForeignKey(User, null=True, blank=True)
    first_name = models.CharField('first name', max_length=30, blank=True, null=True, validators=[not_blank])
    last_name = models.CharField('last name', max_length=30, blank=True, null=True, validators=[not_blank])
    email = models.EmailField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    contact_method = models.SmallIntegerField(choices=CustomerProfile.CONTACT_METHOD, default=CustomerProfile.EMAIL)

    date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(choices=ORDER_STATUSES, default=SUBMITTED)
    ip_address = models.IPAddressField(default="0.0.0.0")  # https://code.djangoproject.com/ticket/5622

    is_pickup = models.BooleanField(default=False)
    shipping_charge = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.0)])

    @property
    def merchandise_total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.price*item.quantity
        return total

    def get_shipping_address(self):
        try:
            return self.shipping_address
        except ObjectDoesNotExist:
            return None

    def get_billing_address(self):
        try:
            return self.billing_address
        except ObjectDoesNotExist:
            return None

    def __unicode__(self):
        return 'Order #%s' % self.id

    def clean(self):
        super(Order, self).clean()
        # if the order is not being picked up, we need the shipping and billing addresses, the email, and possibly
        # the phone field

        if not self.is_pickup:
            if not self.get_shipping_address():
                raise ValidationError(u"The shipping address is required for non-pickup orders.")
            if not self.get_billing_address():
                raise ValidationError(u"The billing address is required for non-pickup orders.")
            if not self.email or is_blank(self.email):
                raise ValidationError(u"The email address is required for non-pickup orders.")

        if self.contact_method == CustomerProfile.PHONE and (not self.phone or is_blank(self.phone)):
            raise ValidationError(u"The preferred contact method is phone, "
                                  u"therefore a valid phone number is required.")

    @property
    def total(self):
        total = self.merchandise_total + self.shipping_charge
        for tax in self.taxes.all():
            total += tax.total
        return total

    def get_absolute_url(self):
        return reverse('order_detail', kwargs={'order_id': self.id})

    @commit_on_success
    def cancel(self):
        """
        Cancels this order.  Orders can only be cancelled before they have shipped.
        """
        if not self.can_be_canceled():
            # user should not see this exception if we're extremely careful about when we present the option to
            # cancel orders.
            raise Exception("Sorry, this order cannot be canceled.")

        # toggle status
        self.status = Order.CANCELLED

        # increment stock counts
        for order_item in self.items.all():
            order_item.item.quantity += order_item.quantity
            order_item.item.save()

        # TODO: reverse any payment authorizations
        self.payment_status = Order.CANCELLED
        self.save()

        # send the order-cancelled signal
        signal_order_cancelled.send(sender=self)

    def can_be_canceled(self):
        return self.status in [Order.SUBMITTED, Order.PROCESSED]


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items")
    item = models.ForeignKey(ProductInstance)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    # I suppose the item could technically be free
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])

    def get_absolute_url(self):
        return self.item.product.get_absolute_url()

    @property
    def total(self):
        return self.quantity * self.price

    @property
    def name(self):
        return self.item.product.name

    @property
    def sku(self):
        return self.item.sku

    def __unicode__(self):
        return self.item.product.name


class OrderBillingAddress(AbstractAddress):
    """
    The billing address associated with an order.  There can be one per order.
    """
    order = models.OneToOneField(Order, related_name='billing_address')


class OrderShippingAddress(AbstractAddress):
    """
    The shipping address associated with an order.  There can only be one per order.
    """
    order = models.OneToOneField(Order, related_name='shipping_address')


class OrderTax(models.Model):
    """
    A tax (eg GST or PST) that has been applied to an order.
    """
    order = models.ForeignKey(Order, related_name="taxes")
    name = models.CharField(max_length=20)
    rate = models.DecimalField(max_digits=7, decimal_places=4, validators=[MinValueValidator(0.0)])  # percentage
    total = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.0)])


class PaymentMethod(models.Model):

    amount = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])

    class Meta:
        abstract = True


class CreditCardPayment(PaymentMethod):
    """
    Represents a credit-card payment processed through this site.
    """
    AUTHORIZED = 1    # funds have been authorized
    CAPTURED = 2      # funds have been captured
    CANCELLED = 3     # the order was cancelled before any money changed hands

    PAYMENT_STATUSES = ((AUTHORIZED, 'Funds Authorized'),
                        (CAPTURED, 'Funds Captured'),
                        (CANCELLED, 'Transaction Cancelled'))

    MASTERCARD = 1
    VISA = 2

    CARD_TYPES = ((MASTERCARD, 'MasterCard'),
                  (VISA, 'VISA'))

    order = models.OneToOneField(Order)  # an order can have at most one credit-card payment
    transaction_id = models.CharField(max_length=20, validators=[not_blank])
    token = models.CharField(max_length=4, validators=[not_blank], help_text="The last 4 digits of the credit card")
    status = models.SmallIntegerField(choices=PAYMENT_STATUSES)
    card_type = models.SmallIntegerField(choices=CARD_TYPES)


class GiftCardPayment(PaymentMethod):
    """
    Represents a gift-card payment.
    """
    AUTHORIZED = 1
    CAPTURED = 2
    CANCELLED = 3

    # I am assuming that a gift card transaction can have the same states as a credit card transaction.  I suspect that
    # this is not exactly true, but it's a starting point.
    PAYMENT_STATUSES = ((AUTHORIZED, 'Funds Authorized'),
                        (CAPTURED, 'Funds Captured'),
                        (CANCELLED, 'Transaction Cancelled'))

    order = models.ForeignKey(Order, related_name='gift_cards')
    transaction_id = models.CharField(max_length=20, validators=[not_blank])  # assumption
    status = models.SmallIntegerField(choices=PAYMENT_STATUSES)
    card_number = models.CharField(max_length=16, validators=[not_blank])     # not sure if we'll have to store the entire card number