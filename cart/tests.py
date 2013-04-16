"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from models import CartItem
from catalogue.tests import create_product
from django.core.exceptions import ValidationError
from django.test.client import Client


class CartItemTest(TestCase):

    def testCreate(self):
        cart_id = 'a'*50
        product = create_product()
        ci = create_cart_item(quantity=2, cart_id=cart_id, product=product)
        self.assertEqual(2, ci.quantity)
        self.assertEqual(cart_id, ci.cart_id)
        self.assertIsNotNone(ci.date_added)

    def testQuantity(self):
        # test that quantity must be greater than zero
        for quantity in [0, -1, -18]:
            with self.assertRaises(ValidationError) as cm:
                create_cart_item(quantity=quantity)
            self.assertIn("Ensure this value is greater than or equal to 1", str(cm.exception))

        # test that quantity defaults to 1
        product = create_product()
        ci = CartItem(product=product, cart_id=CartItem.generate_cart_id())
        self.assertEqual(1, ci.quantity)

        # test that the quantity cannot be nulled out
        with self.assertRaises(ValidationError) as cm:
            create_cart_item(quantity=None)
        self.assertIn("This field cannot be null", str(cm.exception))

    def testCartId(self):
        # def test that every character that can go into a cart-id can be saved to the database field
        for char in CartItem.CART_ID_CHARS:
            cart_id = char
            ci = create_cart_item(cart_id=cart_id)
            self.assertEqual(cart_id, ci.cart_id)

        # test that the cart id cannot be none, and has no default
        with self.assertRaises(ValidationError) as cm:
            ci = CartItem(cart_id=None, product=create_product(), quantity=2)
            ci.full_clean()
        self.assertIn("This field cannot be null", str(cm.exception))

        with self.assertRaises(ValidationError) as cm:
            ci = CartItem(product=create_product(), quantity=2)
            ci.full_clean()
        self.assertIn("This field cannot be blank", str(cm.exception))


    def testPrice(self):
        # regular priced item
        product = create_product(price=15.0)
        ci = create_cart_item(quantity=4, product=product)
        self.assertEqual(15, ci.price)
        self.assertEqual(60, ci.total())
        self.assertIsNone(ci.sale_price)
        ci.quantity = 1
        ci.full_clean()
        ci.save()
        self.assertEqual(15, ci.total())

        # sale priced item
        product = create_product(price=25, sale_price=15)
        ci = create_cart_item(quantity=3, product=product)
        self.assertEqual(25, ci.price)
        self.assertEqual(15, ci.sale_price)
        self.assertEqual(45, ci.total())
        ci.quantity = 4
        ci.full_clean()
        ci.save()
        self.assertEqual(60, ci.total())

    def testGetAbsoluteUrl(self):
        product = create_product()
        ci = create_cart_item(product=product)
        url = ci.get_absolute_url()
        self.assertEqual(product.get_absolute_url(), url)
        c = Client()
        response = c.get(url)
        self.assertEqual(200, response.status_code)

    def testAugmentQuantity(self):
        ci = create_cart_item(quantity=2)
        ci.augment_quantity(3)
        # assert that the new value was properly saved
        ci = CartItem.objects.get(id=ci.id)
        self.assertEqual(5, ci.quantity)

    def testGenerateCartId(self):
        for i in xrange(500):
            cart_id = CartItem.generate_cart_id()
            self.assertIsNotNone(cart_id)
            self.assertEqual(50, len(cart_id))


def create_cart_item(**kwargs):
    cart_id = kwargs.pop('cart_id', None)

    if not cart_id:
        cart_id = CartItem.generate_cart_id()

    product = kwargs.pop('product', None)

    if not product:
        product = create_product()

    quantity = kwargs.pop('quantity', 1)
    if len(kwargs) > 0:
        raise Exception("Extra keyword args in create_cart_item: %s" % kwargs)

    ci = CartItem(cart_id=cart_id, product=product, quantity=quantity)
    ci.full_clean()
    ci.save()
    return ci
