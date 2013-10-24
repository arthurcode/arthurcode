from django.db import models
from catalogue.models import ProductInstance
from django.core.validators import MinValueValidator
import random


class CartItem(models.Model):
    CART_ID_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789!@#$%^&*()'
    SUBCLASS_ERROR = Exception('Subclasses must override')

    cart_id = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['date_added']

    def total(self):
        price = self.sale_price or self.price
        return self.quantity * price

    def name(self):
        raise self.SUBCLASS_ERROR

    @property
    def price(self):
        raise self.SUBCLASS_ERROR

    @property
    def sale_price(self):
        raise self.SUBCLASS_ERROR

    @property
    def sku(self):
        raise self.SUBCLASS_ERROR

    def get_absolute_url(self):
        raise self.SUBCLASS_ERROR

    def augment_quantity(self, quantity):
        self.quantity += int(quantity)
        self.save()

    def check_stock(self):
        raise self.SUBCLASS_ERROR

    def __unicode__(self):
        return u'cart item %d' % self.id

    @classmethod
    def generate_cart_id(cls):
        cart_id = ''
        cart_id_length = 50
        for y in range(cart_id_length):
            cart_id += CartItem.CART_ID_CHARS[random.randint(0, len(CartItem.CART_ID_CHARS) - 1)]
        return cart_id

    @classmethod
    def get_insufficient_stock_msg(cls, in_stock):
        if in_stock <= 0:
            return u"Sorry, this product is now out of stock."
        elif in_stock == 1:
            return u"Sorry, there is only 1 left in stock."
        else:
            return u"Sorry, there are only %d left in stock." % in_stock


class ProductCartItem(CartItem):
    item = models.ForeignKey(ProductInstance, unique=False)

    def name(self):
        return self.item.product.name

    @property
    def price(self):
        return self.item.product.price

    @property
    def sale_price(self):
        return self.item.product.sale_price

    @property
    def sku(self):
        return self.item.sku

    def get_absolute_url(self):
        return self.item.product.get_absolute_url()

    def check_stock(self):
        """
        Checks if there is enough stock to satisfy this cart-item request.
        """
        if self.quantity > self.item.quantity:
            return "%s Please adjust your cart." % CartItem.get_insufficient_stock_msg(self.item.quantity)
        return None

    def __unicode__(self):
        return unicode(self.item)