from django.db import models
from catalogue.models import Product
from django.core.validators import MinValueValidator
import random


class CartItem(models.Model):
    cart_id = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)
    quantity = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    product = models.ForeignKey(Product, unique=False)

    class Meta:
        ordering = ['date_added']

    def total(self):
        price = self.sale_price or self.price
        return self.quantity * price

    def name(self):
        return self.product.name

    @property
    def price(self):
        return self.product.price

    @property
    def sale_price(self):
        return self.product.sale_price

    def get_absolute_url(self):
        return self.product.get_absolute_url()

    def augment_quantity(self, quantity):
        self.quantity += int(quantity)
        self.save()

    def __unicode__(self):
        return self.product.name

    @classmethod
    def generate_cart_id(cls):
        cart_id = ''
        characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789!@#$%^&*()'
        cart_id_length = 50
        for y in range(cart_id_length):
            cart_id += characters[random.randint(0, len(characters) - 1)]
        return cart_id