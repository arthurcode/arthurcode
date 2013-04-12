from django.test import TestCase
from blog.tests import Counter
from catalogue.models import Category, Product
from datetime import datetime
from django.test.client import Client
from blog import validators
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError


class CategoryTest(TestCase):

    def setUp(self):
        self.c = Client()

    def tearDown(self):
        pass

    def testDefaults(self):
        category = Category(name="Some Category", slug="some-category", parent=None, description="description")
        self.assertTrue(category.is_active)
        today = datetime.today()
        #self.assertEqual(today, category.updated_at)
        # TODO: why are the created_at and updated_at fields coming up as None?

    def testMakeRootCategory(self):
        self.assertEqual(0, Category.objects.root_nodes().count())
        category = create_category(parent=None)
        self.assertEqual(1, Category.objects.root_nodes().count())
        self.assertIsNone(category.parent)

        url = category.get_absolute_url()
        self.assertIsNotNone(url)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)

    def testMakeChildCategory(self):
        root = create_root_category()
        child = create_category(parent=root)
        self.assertEqual(2, Category.objects.count())
        self.assertEqual(child, root.get_children()[0])

        url = child.get_absolute_url()
        self.assertIsNotNone(url)
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)

    def testProductCount(self):
        # returns the number of product in this exact category
        root = create_root_category()
        self.assertEqual(0, root.product_count())


class ProductTest(TestCase):

    def setUp(self):
        self.blanks = ["", u""]

    def testProductUPC(self):
        valid_upcs = ['111111111111', '012345678912']
        invalid_upcs = ['hi', 'rightlength2', '0123456789', '012345678901234']

        for upc in valid_upcs:
            product = create_product(upc=upc)
            self.assertEqual(upc, product.upc)

        for upc in invalid_upcs:
            with self.assertRaises(ValidationError) as cm:
                create_product(upc=upc)
            self.assertIn(validators.ERROR_UPC, str(cm.exception))

        for upc in self.blanks:
            with self.assertRaises(ValidationError) as cm:
                create_product(upc=upc)
            self.assertIn(validators.ERROR_BLANK, str(cm.exception))

    def testDefaults(self):
        category = create_category()
        product = Product(name="Product", slug="slug", upc="000000000000", category=category, short_description="short",
                          long_description="long", price="5.00", brand="XYZ", quantity=10)
        product.full_clean()
        product.save()
        self.assertEquals(1, len(Product.objects.all()))
        product = Product.objects.all()[0]

        self.assertTrue(product.is_active)
        self.assertFalse(product.is_featured)
        self.assertFalse(product.is_bestseller)
        self.assertIsNotNone(product.created_at)
        self.assertIsNotNone(product.updated_at)

    def testNoInactiveProductsInActiveCategories(self):
        category = create_category(is_active=True)

        with self.assertRaises(ValidationError) as cm:
            create_product(category=category, is_active=False)
        self.assertIn(Product.ERROR_INACTIVE_PRODUCT_IN_ACTIVE_CATEGORY, str(cm.exception))

        category.is_active = False
        category.full_clean()
        category.save()

        product = create_product(category=category, is_active=False)
        self.assertIsNotNone(product)
        self.assertFalse(product.is_active)

        category = create_category(is_active=True)
        product = create_product(category=category)
        self.assertTrue(product.is_active)
        product.is_active = False

        with self.assertRaises(ValidationError) as cm:
            product.full_clean()
        self.assertIn(Product.ERROR_INACTIVE_PRODUCT_IN_ACTIVE_CATEGORY, str(cm.exception))

    def testGetAbsoluteURL(self):
        product = create_product()
        url = product.get_absolute_url()
        response = Client().get(url)
        self.assertEquals(200, response.status_code)

    def testQuantity(self):
        # quantity must be an integer >= 0
        category = create_root_category()
        valid_quantities = [0, 1, 9999, 10000]

        for quantity in valid_quantities:
            product = create_product(quantity=quantity, category=category)
            self.assertEqual(quantity, product.quantity)

        # I can't run more than one of these tests per test method because this type of error causes my transaction
        # to abort.  All code in a single test method runs inside a single transaction, and this code effectively
        # kills the transaction
        with self.assertRaises(IntegrityError) as cm:
            create_product(quantity=-1, category=category)
        self.assertIn("violates check constraint", str(cm.exception))

    def testPrices(self):
        # price cannot be zero
        valid_prices = [0.01, 5, 10, 5.68, 29.99]
        invalid_prices = [0, -1.32, -0.01]

        for price in valid_prices:
            product = create_product(price=price)
            self.assertEquals(product.price, price)
            product = create_product(price=1000, sale_price=price)
            self.assertEqual(price, product.sale_price)

        for price in invalid_prices:
            with self.assertRaises(ValidationError) as cm:
                create_product(price=price)
            self.assertIn("Ensure this value is greater than or equal to 0.01", str(cm.exception))
            with self.assertRaises(ValidationError) as cm:
                create_product(price=10000, sale_price=price)
            self.assertIn("Ensure this value is greater than or equal to 0.01", str(cm.exception))


COUNTER = Counter()


def create_root_category(**kwargs):
    kwargs['parent'] = None
    return create_category(**kwargs)


def create_category(**kwargs):
    count = COUNTER.next()
    parent = kwargs.get('parent', None)
    name = kwargs.get('name', 'category%d' % count)
    slug = kwargs.get('slug', 'category%d-slug' % count)
    description = kwargs.get('description', 'Category description.')
    is_active = kwargs.get('is_active', True)
    category = Category(parent=parent, name=name, slug=slug, description=description, is_active=is_active)

    category.full_clean()
    category.save()
    return category


def create_product(**kwargs):
    count = COUNTER.next()
    category = kwargs.get('category', None)
    name = kwargs.get('name', 'Product%d' % count)
    slug = kwargs.get('slug', 'product%d-slug' % count)
    upc = kwargs.get('upc', '012345678901')
    brand = kwargs.get('brand', 'XYZ Brand')
    short_desc = kwargs.get('short_desc', "The short description.")
    long_desc = kwargs.get('long_desc', "The long description.")
    price = kwargs.get('price', '5.99')
    sale_price = kwargs.get('sale_price', None)
    quantity = kwargs.get('quantity', 10)
    is_active = kwargs.get('is_active', True)

    if not category:
        category = create_root_category(name='Dummy Category %d' % count)

    product = Product(category=category, name=name, slug=slug, upc=upc, brand=brand, short_description=short_desc,
                      long_description=long_desc, price=price, quantity=quantity, is_active=is_active,
                      sale_price=sale_price)
    product.full_clean()
    product.save()
    return product
