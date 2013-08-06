from django.db import models
from django.core.validators import MinValueValidator
from mptt.models import MPTTModel, TreeForeignKey
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db import transaction

from utils.validators import not_blank, valid_upc


class Category(MPTTModel, models.Model):
    ERROR_ACTIVE_CATEGORY_INACTIVE_PARENT = "An inactive category cannot have an active subcategory"

    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            help_text='Parent category. Do not re-parent a category unless you REALLY know what you are doing.')
    name = models.CharField(max_length=50, unique=True, validators=[not_blank],
                            help_text='Should make sense when prefixed with the word "All"')
    slug = models.SlugField(max_length=50,
                            unique=True,
                            help_text='Unique value for category page URL, created from name.',
                            validators=[not_blank])
    description = models.TextField(help_text='Content for description meta tag', validators=[not_blank])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering=['tree_id', 'lft']

    class MPTTMeta:
        order_insertion_by = ['name']

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalogue_category', kwargs={'category_slug': self.slug})

    def product_count(self):
        """
        Returns the number of products that are linked directly to this category.  This does not count products
        that are in subcategories of this product.
        """
        return self.product_set.count()

    @transaction.commit_on_success
    def set_is_active(self, is_active):
        """
        When a category is activated or deactivated, all of its subcategories and products must be activated or
        deactivated as well.
        """
        subcategories = self.get_descendants(include_self=True)
        products = Product.objects.filter(category__in=subcategories)

        for category in subcategories:
            category.is_active = is_active
            category.full_clean()
            category.save()

        for product in products:
            product.is_active = is_active
            product.full_clean()
            product.save()

    def clean(self):
        if self.parent_id and self.is_active and not self.parent.is_active:
            raise ValidationError(Category.ERROR_ACTIVE_CATEGORY_INACTIVE_PARENT)


class ActiveProductsManager(models.Manager):
    def get_query_set(self):
        return super(ActiveProductsManager, self).get_query_set().filter(is_active=True)


class Award(models.Model):

    name = models.CharField(max_length=50, validators=[not_blank])
    slug = models.SlugField(max_length=50, unique=True, help_text='Unique value for award page URL, created from name.',
                            validators=[not_blank])
    short_description = models.CharField(max_length=500)
    long_description = models.TextField(help_text='May contain html')

    def __unicode__(self):
        return self.name


class AwardInstance(models.Model):
    award = models.ForeignKey(Award)
    date = models.DateField(help_text='The date (or year) the award was given out.')

    def __unicode__(self):
        return unicode(self.award) + " (" + str(self.date.year) + ")"


class Brand(models.Model):

    name = models.CharField(max_length=50, validators=[not_blank])
    slug = models.SlugField(max_length=50, unique=True, help_text='Unique value for brand page URL, created from name.',
                            validators=[not_blank])
    short_description = models.CharField(max_length=500)
    long_description = models.TextField(help_text='May contain html')

    def __unicode__(self):
        return self.name


class Theme(models.Model):

    name = models.CharField(max_length=50, validators=[not_blank])
    slug = models.SlugField(max_length=50, unique=True, validators=[not_blank])
    short_description = models.CharField(max_length=500)

    def __unicode__(self):
        return self.name


class Product(models.Model):

    ERROR_INACTIVE_PRODUCT_IN_ACTIVE_CATEGORY = "An inactive product cannot be in an active category."
    ERROR_ACTIVE_PRODUCT_IN_INACTIVE_CATEGORY = "An active product cannot be in an inactive category."
    ERROR_SALE_PRICE_MORE_THAN_PRICE = "The sale price must be less than or equal to the product price."

    objects = models.Manager()
    active = ActiveProductsManager()

    name = models.CharField(max_length=255, unique=True, validators=[not_blank])
    slug = models.SlugField(max_length=255,
                            unique=True,
                            help_text='Unique value for product page URL, created from name.',
                            validators=[not_blank])
    brand = models.ForeignKey(Brand, related_name="products")
    upc = models.CharField(max_length=12, validators=[valid_upc])
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    sale_price = models.DecimalField(max_digits=9,
                                     decimal_places=2,
                                     blank=True,
                                     null=True,
                                     validators=[MinValueValidator(0.01)])
    is_active = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_box_stuffer = models.BooleanField(default=False)
    is_green = models.BooleanField(default=False, help_text='Indicates if this is an eco-friendly product.')

    short_description = models.CharField(max_length=500)
    long_description = models.TextField()
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category)

    awards = models.ManyToManyField(AwardInstance, related_name="products", blank=True, null=False)
    themes = models.ManyToManyField(Theme, related_name="products", blank=True, null=False)

    def clean(self):
        if not self.is_active and self.category_id and self.category.is_active:
            raise ValidationError(Product.ERROR_INACTIVE_PRODUCT_IN_ACTIVE_CATEGORY)

        if self.is_active and self.category_id and not self.category.is_active:
            raise ValidationError(Product.ERROR_ACTIVE_PRODUCT_IN_INACTIVE_CATEGORY)

        if self.sale_price and self.price and self.sale_price >= self.price:
            raise ValidationError(Product.ERROR_SALE_PRICE_MORE_THAN_PRICE)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('catalogue_product', kwargs={'slug': self.slug})

    def deactivate(self):
        self.category = get_inactive_category()
        self.is_active = False
        self.full_clean()
        self.save()

    def percent_savings(self):
        if self.sale_price:
            return (self.price - self.sale_price) * 100 / self.price
        return 0

    @property
    def is_award_winner(self):
        return self.awards and self.awards.count() > 0

    def get_rating(self):
        """
        Returns this product's average review rating.  Returns None if there are no reviews.
        """
        return self.reviews.aggregate(models.Avg('rating'))['rating__avg']

    @classmethod
    def select_current_price(cls, queryset):
        return queryset.extra(select={"current_price": "COALESCE(sale_price, price)"})


class ProductImage(models.Model):
    """
    Represents an image or 'view' of a particular product.  A product can have zero or more images associated with
    it.  Product thumbnails are not included in this set.
    """
    PATH_MAX_LENGTH = 100
    ALT_TEXT_MAX_LENGTH = 200

    product = models.ForeignKey(Product, related_name="images")
    is_primary = models.BooleanField(default=False,
                                     help_text=u"The primary image is the first to load on the product page."
                                               u" It should be the image that best represents the product.")
    path = models.CharField(max_length=PATH_MAX_LENGTH,
                            help_text=u"Path to the medium resolution image, relative to the static url")
    detail_path = models.CharField(max_length=PATH_MAX_LENGTH,
                                   help_text=u"Path to the high resolution image, relative to the static url.")
    alt_text = models.CharField(max_length=ALT_TEXT_MAX_LENGTH, help_text=u"HTML image alt text.")

    def __unicode__(self):
        return self.path


def get_inactive_category():
    """
    Returns a special Category instance that can be used to store products that are no longer active.  We don't want
    inactive products to live in active categories, but we will need to deactivate products and they need to reference
    a category.
    """
    params = {
        'name': 'Inactive Category',
        'slug': 'inactive-category',
        'is_active': False,
        'description': 'This category stores all products that are no longer active.',
        'parent': None
    }
    category, _ = Category.objects.get_or_create(**params)
    return category

# register any signals for this app
