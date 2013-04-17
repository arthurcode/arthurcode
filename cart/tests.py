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
from bs4 import BeautifulSoup
from cart.forms import ProductAddToCartForm
import cartutils
import random


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


class AddToCartFormTest(TestCase):

    def setUp(self):
        self.c = Client()

    def testGetAddToCartForm(self):
        product = create_product(quantity=2)
        response = self.c.get(product.get_absolute_url())
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        form = soup.find('form', 'add-to-cart')
        self.assertIsNotNone(form)

        # test that there is only one visible label (for the quantity field)
        labels = form.find_all('label')
        self.assertEqual(1, len(labels))
        label = labels[0]
        self.assertIn("Quantity", label.text)
        self.assertEqual('id_quantity', label.attrs['for'])

        # test that the default quantity value is 1
        quantity_input = form.find('input', {'id': 'id_quantity'})
        self.assertIsNotNone(quantity_input)
        self.assertEqual('1', quantity_input.attrs['value'])

        # test that the hidden product slug field is properly filled out
        slug_input = form.find('input', {'id': 'id_product_slug'})
        self.assertIsNotNone(slug_input)
        self.assertEqual(product.slug, slug_input.attrs['value'])

    def testAddToCartQuantityError(self):
        product = create_product()
        url = product.get_absolute_url()

        # make sure the test cookie is set
        self.c.get(url)

        data = add_to_cart_post_data(quantity='aa', product=product)
        response = self.c.post(url, data, follow=True)

        # there was a form error, so the original product page should have been rendered
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'product_detail.html')
        self.assertContains(response, product.name)
        soup = BeautifulSoup(response.content)
        form = soup.find('form', 'add-to-cart')
        quantity_label = form.find('label', {'for': 'id_quantity'})
        error = quantity_label.find('span', 'error')
        self.assertIn('Please enter a valid quantity', error.text)

        data = add_to_cart_post_data(quantity='0', product=product)
        response = self.c.post(url, data, follow=True)

        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'product_detail.html')
        self.assertContains(response, product.name)
        soup = BeautifulSoup(response.content)
        form = soup.find('form', 'add-to-cart')
        quantity_label = form.find('label', {'for': 'id_quantity'})
        error = quantity_label.find('span', 'error')
        self.assertIn('Ensure this value is greater than or equal to 1', error.text)

    def testCookiesNotEnabled(self):
        # the test cookie hasn't been set, so the cookie test should fail
        product = create_product()
        url = product.get_absolute_url()
        data = add_to_cart_post_data(quantity='2', product=product)
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'product_detail.html')
        self.assertContains(response, product.name)

        # the cookie error will be displayed in the quantity field
        soup = BeautifulSoup(response.content)
        form = soup.find('form', 'add-to-cart')
        quantity_label = form.find('label', {'for': 'id_quantity'})
        error = quantity_label.find('span', 'error')
        self.assertIn(ProductAddToCartForm.ERROR_COOKIES_DISABLED, error.text)

    def testSuccess(self):
        product = create_product(quantity=5)
        url = product.get_absolute_url()
        self.c.get(url)  # set the test cookie

        data = add_to_cart_post_data(quantity='2', product=product)
        response = self.c.post(url, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'cart.html')

        cart_id = get_cart_id(self.c)
        cart_items = CartItem.objects.filter(cart_id=cart_id)
        self.assertEqual(1, cart_items.count())
        item = cart_items[0]
        self.assertEqual(product, item.product)
        self.assertEqual(2, item.quantity)


class ShoppingCartTest(TestCase):

    def setUp(self):
        self.c = Client()

    def testOneCartItemPerProduct(self):
        product = create_product()
        add_to_cart(self.c, product, 2)
        cart_id = get_cart_id(self.c)
        cart_items = CartItem.objects.filter(cart_id=cart_id)
        self.assertEqual(1, cart_items.count())
        item = cart_items[0]
        self.assertEqual(product, item.product)
        self.assertEqual(2, item.quantity)
        date_added = item.date_added

        add_to_cart(self.c, product, 3)
        cart_items = CartItem.objects.filter(cart_id=cart_id)
        self.assertEqual(1, cart_items.count())
        item = cart_items[0]
        self.assertEqual(product, item.product)
        self.assertEqual(5, item.quantity)
        self.assertEqual(date_added, item.date_added)

    def testCartItemOrdering(self):
        characters = 'abcdefghijklmnopqrstuvwxyz'
        products = []

        for x in xrange(20):
            name = ''
            for i in xrange(20):
                name += characters[random.randint(0, len(characters)-1)]
            product = create_product(name=name, slug=name)
            self.assertEqual(name, product.name)
            self.assertEqual(name, product.slug)
            add_to_cart(self.c, product, 1)
            products.append(product)

        cart_id = get_cart_id(self.c)
        cart_items = CartItem.objects.filter(cart_id=cart_id)
        self.assertEqual(len(products), cart_items.count())

        # the cart items should be ordered by the date they were added
        for (product, cart_item) in zip(products, cart_items):
            self.assertEqual(product, cart_item.product)
            self.assertEqual(product.price, cart_item.price)
            self.assertEqual(product.sale_price, cart_item.sale_price)

    def testUniqueCarts(self):
        c1 = Client()
        c2 = Client()
        product = create_product()

        add_to_cart(c1, product, 2)
        add_to_cart(c2, product, 3)
        cart_items_1 = CartItem.objects.filter(cart_id=get_cart_id(c1))
        cart_items_2 = CartItem.objects.filter(cart_id=get_cart_id(c2))
        self.assertEqual(1, cart_items_1.count())
        self.assertEqual(1, cart_items_2.count())

        self.assertEqual(2, cart_items_1[0].quantity)
        self.assertEqual(3, cart_items_2[0].quantity)


def get_cart_id(client):
    return client.session[cartutils.CART_ID_SESSION_KEY]


def add_to_cart(client, product, quantity):
    client.get(product.get_absolute_url()) # set test cookie
    data = add_to_cart_post_data(product=product, quantity=quantity)
    return client.post(product.get_absolute_url(), data, follow=True)


def add_to_cart_post_data(**kwargs):
    product = kwargs.pop('product')
    quantity = kwargs.pop('quantity')
    if len(kwargs) > 0:
        raise Exception('Extra keyword args add_to_cart_post_data: %s' % kwargs)

    return {
        'quantity': str(quantity),
        'product_slug': product.slug
    }


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
