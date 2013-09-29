from django.db import models
from django.core.validators import MinValueValidator
from mptt.models import MPTTModel, TreeForeignKey
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django_countries import CountryField

from utils.validators import not_blank, valid_sku


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
    """
    Select products that are active.  Assume that each product has at least one instance associated with it.  It's too
    expensive to check that the product has instances associated with it every single time.
    """
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

    def get_absolute_url(self):
        return reverse('award', kwargs={'award_slug': self.slug})


class AwardInstance(models.Model):
    award = models.ForeignKey(Award, related_name='instances')
    date = models.DateField(help_text='The date (or year) the award was given out.')

    def __unicode__(self):
        return unicode(self.award) + " (" + str(self.date.year) + ")"


class Brand(models.Model):

    name = models.CharField(max_length=50, validators=[not_blank])
    slug = models.SlugField(max_length=50, unique=True, help_text='Unique value for brand page URL, created from name.',
                            validators=[not_blank])
    short_description = models.CharField(max_length=500, help_text='May be used for meta description tags, so no html')
    long_description = models.TextField(help_text='May contain html')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('brand', kwargs={'brand_slug': self.slug})


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
    ERROR_MAX_AGE_TOO_SMALL = "The maximum age is smaller than the minimum age."

    objects = models.Manager()
    active = ActiveProductsManager()

    name = models.CharField(max_length=255, unique=True, validators=[not_blank])
    slug = models.SlugField(max_length=255,
                            unique=True,
                            help_text='Unique value for product page URL, created from name.',
                            validators=[not_blank])
    brand = models.ForeignKey(Brand, related_name="products")
    price = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0.01)])
    sale_price = models.DecimalField(max_digits=9,
                                     decimal_places=2,
                                     blank=True,
                                     null=True,
                                     validators=[MinValueValidator(0.01)])
    is_active = models.BooleanField(default=True, db_index=True)
    is_bestseller = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_box_stuffer = models.BooleanField(default=False)
    is_green = models.BooleanField(default=False, help_text='Indicates if this is an eco-friendly product.')
    country_of_origin = CountryField()

    meta_description = models.CharField(max_length=200, help_text='Text for the meta description tag.',
                                        validators=[not_blank])
    short_description = models.CharField(max_length=700, help_text='You can use markdown formatting')
    long_description = models.TextField(blank=True, help_text='You can use markdown formatting')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category)

    awards = models.ManyToManyField(AwardInstance, related_name="products", blank=True, null=False)
    themes = models.ManyToManyField(Theme, related_name="products", blank=True, null=False)

    min_age = models.PositiveIntegerField(help_text=u"The minimum age a person should be to use this product",
                                          default=0)
    max_age = models.PositiveIntegerField(help_text=u"The oldest age this product would appeal to."
                                                    u" Please put some thought into this because it is important "
                                                    u"for filtering.  Leave blank if there really is no max age",
                                          null=True, blank=True)

    # dimensions
    weight = models.DecimalField(decimal_places=3, max_digits=6, help_text="The weight of the assembled product, in Kg")

    def clean(self):
        if not self.is_active and self.category_id and self.category.is_active:
            raise ValidationError(Product.ERROR_INACTIVE_PRODUCT_IN_ACTIVE_CATEGORY)

        if self.is_active and self.category_id and not self.category.is_active:
            raise ValidationError(Product.ERROR_ACTIVE_PRODUCT_IN_INACTIVE_CATEGORY)

        if self.sale_price and self.price and self.sale_price >= self.price:
            raise ValidationError(Product.ERROR_SALE_PRICE_MORE_THAN_PRICE)

        if self.max_age and self.max_age < self.min_age:
            raise ValidationError(Product.ERROR_MAX_AGE_TOO_SMALL)

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

    rating = -1   # None is a valid rating for products without any reviews

    def get_rating(self):
        """
        Returns this product's average review rating.  Returns None if there are no reviews.
        """
        if self.rating == -1:
            self.rating = self.reviews.aggregate(models.Avg('rating'))['rating__avg']
        return self.rating

    @classmethod
    def select_current_price(cls, queryset):
        return queryset.extra(select={"current_price": "COALESCE(sale_price, price)"})

    def in_stock(self):
        """
        Returns True if any of this product's instances (options) are in stock.  Assume that self.instances.all()
        has been pre-fetched or is cached.
        """
        for instance in self.instances.all():
            if instance.quantity > 0:
                return True
        return False

    def has_options(self):
        """
        Returns True if this product has any options, such as size and/or color.  Assume that self.instances.all()
        has been pre-fetched or is cached.
        """
        return len(self.instances.all()) > 0

    def get_options(self):
        """
        Returns a mapping from option category --> the unique set of ProductOptions in that category that apply
        to this product.  The size options will be sorted in order of increasing sort-index.

        Assumes that product.instances.all() and instance.options.all() have been pre-fetched and are cached.
        """
        option_map = {}

        for instance in self.instances.all():
            for option in instance.options.all():
                category = option.get_category_display()
                if category not in option_map:
                    option_map[category] = [option]
                else:
                    option_map[category].append(option)
        return option_map

    def get_breadcrumbs(self):
        """
        Returns the category breadcrumbs for this product, in order of most general category to the most specific
        category.
        """
        return self.category.get_ancestors(ascending=False, include_self=True)  # will always have at least one entry

    def get_thumbnail(self):
        # assume that self.images.all() has been pre-fetched using the prefetch_related() function
        # this optimization is very important for the catalogue pages, since we don't want to query the DB for
        # every single product, looking for its thumbnail image
        images = self.images.all()
        thumbs = []

        for image in images:
            if image.thumb_path:
                if image.is_primary:
                    return image
                thumbs.append(image)

        if thumbs:
            return thumbs[0]
        return None



class Specification(models.Model):
    """
    Holds a product specification.  Could be something like wattage, material construction, unpacked dimensions, etc.
    Typically product specifications stored here will be things that are not applicable to all products, and thus
    couldn't be turned into a model field.
    """
    product = models.ForeignKey(Product, related_name="specifications")
    key = models.CharField(max_length=50, validators=[not_blank])
    value = models.CharField(max_length=75, validators=[not_blank])


class Dimension(models.Model):
    """
    Holds a product dimension.  The key value pair will typically be displayed as a dt, dd pair in a definition list.
    The key can be something specific like 'length', or it can be something like 'L x W x H'
    """
    class Meta:
        # we want the dimensions to appear in the same order as they are added on the admin page
        ordering = ['id']

    product = models.ForeignKey(Product, related_name="dimensions")
    key = models.CharField(max_length=50, validators=[not_blank])
    value = models.CharField(max_length=75, validators=[not_blank])


class ProductOption(models.Model):
    """
    A product option can be something like a size or color option.  This functions more like an abstract base class,
    but in order to simplify the corresponding queries I haven't made it abstract.  Screw you django.
    """
    COLOR = 1
    SIZE = 2
    OPTION_CATEGORIES = ((COLOR, 'color'),
                         (SIZE, 'size'))

    name = models.CharField(max_length=50, validators=[not_blank],
                            help_text="Full product option name, as it should appear on invoices")
    category = models.IntegerField(choices=OPTION_CATEGORIES)

    class Meta:
        unique_together = ('category', 'name')

    def __unicode__(self):
        return self.name


class Color(ProductOption):
    html = models.CharField(max_length=25, validators=[not_blank], help_text="HTML color hex string, or color name.")

    def clean(self):
        if self.category != ProductOption.COLOR:
            raise ValidationError(u"Category must be 'color'")


class Size(ProductOption):
    short_name = models.CharField(max_length=50, validators=[not_blank],
                                  help_text="Abbreviation for this size, as will appear in the sizing select box.  Eg: 'L', 'M'")
    sort_index = models.IntegerField(help_text="An index used to sort sizes in increasing order.  Eg. 'S' should have a smaller index than 'M'")

    def clean(self):
        if self.category != ProductOption.SIZE:
            raise ValidationError(u"Category must be 'size'")


class ProductInstance(models.Model):
    """
    A product instance is a product together with zero or more product options.  An instance has a unique SKU derived
    from the base SKU of the product together with the SKUs of any applicable product options.  ProductInstances have
    stock counts and can be sold, Products cannot.  ProductInstances are grouped together on category pages since they
    differ only by size/color options (for example).
    """
    product = models.ForeignKey(Product, related_name="instances")
    quantity = models.PositiveIntegerField()
    sku = models.CharField(max_length=10, validators=[valid_sku], unique=True)
    options = models.ManyToManyField(ProductOption, blank=True)

    def __unicode__(self):
        string = unicode(self.product)
        for option in self.options.all():
            string += " (%s)" % unicode(option)
        return string

    def get_best_image(self):
        """
        Of all the images linked to the main product, choose the one that best represents this product instance.
        Returns an instance of ProductImage.
        """
        if not self.product.images.count():
            return None

        specific_images = self.product.images.filter(option__in=self.options.all()).order_by('-is_primary', 'id')
        if specific_images.exists():
            return specific_images[0]
        return self.product.images.order_by('-is_primary', 'id')[0]

    @property
    def name(self):
        return self.product.name

    def get_absolute_url(self):
        return self.product.get_absolute_url()


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

    # not all product images require a corresponding thumbnail image, but a product SHOULD have at least one thumbnail
    thumb_path = models.CharField(max_length=PATH_MAX_LENGTH,
                                  help_text=u"Path to the thumbnail sized image, relative to the static url.",
                                  blank=True)
    alt_text = models.CharField(max_length=ALT_TEXT_MAX_LENGTH, help_text=u"HTML image alt text.")
    option = models.ForeignKey(ProductOption, help_text=u"The product option this image represents (ie. color).", null=True, blank=True)

    def __unicode__(self):
        return self.path


class RestockNotification(models.Model):
    instance = models.ForeignKey(ProductInstance, related_name="restock_notifications")
    email = models.EmailField(validators=[not_blank], help_text="The email address to notify when this product instance "
                                                                "is back in stock.")

    class Meta:
        unique_together = ('instance', 'email')

    def __unicode__(self):
        return "%s %s" % (self.instance, self.email)


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
