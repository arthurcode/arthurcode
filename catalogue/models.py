from django.db import models
from django.core.validators import MinValueValidator
from mptt.models import MPTTModel, TreeForeignKey
from blog.validators import not_blank
from django.core.urlresolvers import reverse


class Category(MPTTModel, models.Model):
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            help_text='Parent category. Do not re-parent a category unless you REALLY know what you are doing.')
    name = models.CharField(max_length=50, unique=True, validators=[not_blank])
    slug = models.SlugField(max_length=50,
                            unique=True,
                            help_text='Unique value for category page URL, created from name.',
                            validators=[not_blank])
    description = models.TextField(help_text='Content for description meta tag', validators=[not_blank])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering=['tree_id', 'lft']

    class MPTTMeta:
        order_insertion_by = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog_category', kwargs={'category_slug': self.slug})

    def product_count(self):
        """
        Returns the number of products that are linked directly to this category.  This does not count products
        that are in subcategories of this product.
        """
        return self.product_set.count()


class Product(models.Model):
    name = models.CharField(max_length=255, unique=True, validators=[not_blank])
    slug = models.SlugField(max_length=255,
                            unique=True,
                            help_text='Unique value for product page URL, created from name.',
                            validators=[not_blank])
    brand = models.CharField(max_length=50, validators=[not_blank])
    sku = models.CharField(max_length=50, validators=[not_blank])
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    sale_price = models.DecimalField(max_digits=9,
                                     decimal_places=2,
                                     blank=True,
                                     null=True,
                                     validators=[MinValueValidator(0.01)])
    is_active = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    short_description = models.CharField(max_length=500)
    long_description = models.TextField()
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalog_product', kwargs={'slug': self.slug})