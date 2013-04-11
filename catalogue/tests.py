from django.test import TestCase
from blog.tests import Counter
from catalogue.models import Category
from datetime import datetime
from django.test.client import Client


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
