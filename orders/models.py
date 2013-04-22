from django.db import models
from catalogue.models import Product
from django.core.validators import MinValueValidator
from accounts.models import CustomerProfile
from utils.models import AbstractAddress
import decimal
from utils.validators import is_blank
from django.core.exceptions import ValidationError, ObjectDoesNotExist


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

    PHONE = 1
    EMAIL = 2

    CONTACT_METHOD = ((PHONE, 'Phone'),
                      (EMAIL, 'Email'))

    # will be null if the customer checks out as a guest, or if the order is done in-person or over the phone.
    customer = models.ForeignKey(CustomerProfile, null=True, blank=True)
    email = models.EmailField(max_length=50, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    contact_method = models.SmallIntegerField(choices=CONTACT_METHOD, default=EMAIL)

    date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    status = models.SmallIntegerField(choices=ORDER_STATUSES, default=SUBMITTED)
    transaction_id = models.CharField(max_length=20)
    ip_address = models.IPAddressField(default="0.0.0.0")  # https://code.djangoproject.com/ticket/5622

    is_pickup = models.BooleanField(default=False)

    shipping_charge = models.DecimalField(max_digits=9, decimal_places=2, default=0.00,
                                          validators=[MinValueValidator(0.0)])
    sales_tax = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.0)], default=0.00)

    @property
    def merchandise_total(self):
        """
        The total cost of all products in this order, not including tax or shipping.
        """
        total = decimal.Decimal('0.00')
        for item in self.orderitem_set.all():
            total += item.total
        return total

    @property
    def total(self):
        """
        The total amount that will be charged to the customer, including tax and shipping changes.  Apparently
        shipping and handling charges are subject to sales tax!
        """
        return self.merchandise_total + self.shipping_charge + self.sales_tax

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

        if self.contact_method == Order.PHONE and (not self.phone or is_blank(self.phone)):
            raise ValidationError(u"The preferred contact method is phone, "
                                  u"therefore a valid phone number is required.")


class OrderItem(models.Model):
    order = models.ForeignKey(Order)
    product = models.ForeignKey(Product)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    # I suppose the item could technically be free
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    @property
    def total(self):
        return self.quantity * self.price

    @property
    def name(self):
        return self.product.name

    def __unicode__(self):
        return self.product.name


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



