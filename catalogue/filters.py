"""
Contains filters for filtering catalogue queries.
"""
from django.db.models import Q
from catalogue.models import Award, Brand, Theme, Color
from utils.util import to_bool
from decimal import Decimal
from utils.templatetags.extras import currency
from django.db.models import Model
from datetime import datetime, timedelta
from urllib import quote_plus, unquote_plus
from django_countries.countries import OFFICIAL_COUNTRIES

WILDCARD = "any"


class Filter(object):

    filter_key = None  # subclasses must define

    def apply(self, queryset):
        return queryset

    def __unicode__(self):
        raise Exception("Subclasses must override")

    def as_param(self):
        return self.filter_key + "=" + quote_plus(self.value_for_url())

    def value_for_url(self):
        raise Exception("Subclasses must override")


class OnSaleFilter(Filter):

    filter_key = "filterOnSale"

    def __init__(self, on_sale=True):
        self.on_sale = to_bool(on_sale)

    def apply(self, queryset):
        if self.on_sale:
            # return products that are on sale
            return queryset.exclude(sale_price=None)
        else:
            # return products that are not on sale
            return queryset.filter(sale_price=None)

    def __unicode__(self):
        if self.on_sale:
            return u'on sale'
        return u'not on sale'

    def value_for_url(self):
        return str(self.on_sale)


class BooleanFieldFilter(Filter):
    """
    filters on a boolean field on the product model
    """
    field_name = None  # subclasses should override

    def __init__(self, value=True):
        self.value = to_bool(value)

    def apply(self, queryset):
        return queryset.filter(**{self.field_name: self.value})

    def value_for_url(self):
        return str(self.value)


class IsBoxStufferFilter(BooleanFieldFilter):

    filter_key = "filterBoxStuffer"
    field_name = "is_box_stuffer"

    def __unicode__(self):
        if self.value:
            return u'box-stuffers'
        return u'non box-stuffers'


class IsEcoFriendlyFilter(BooleanFieldFilter):

    filter_key = "filterGreen"
    field_name = "is_green"

    def __unicode__(self):
        if self.value:
            return 'eco-friendly'
        return 'non eco-friendly'


class RelatedModelFilter(Filter):

    slug_field = "slug"
    name_field = "name"
    related_name = None  # subclasses must define
    model = None # subclasses must define

    def __init__(self, instance):
        if isinstance(instance, Model):
            self.slug = getattr(instance, self.slug_field)
            self.name = getattr(instance, self.name_field)
        else:
            # assume that we've been given the model slug, the name will be derived if and when it is required
            self.slug = str(instance)

    def apply(self, queryset):
        # return products that are related to the given model, identified by its slug
        return queryset.filter(**{self.related_name + "__" + self.slug_field: self.slug})

    def get_name(self):
        # lookup up the instance name using the slug
        if not hasattr(self, 'name'):
            instance = getattr(self.model, 'objects').filter(**{self.slug_field: self.slug})
            if instance.count() > 0:
                self.name = instance[0].name
            else:
                self.name = self.slug
        return self.name

    def value_for_url(self):
        return self.slug


class AwardFilter(RelatedModelFilter):

    filter_key = "filterAward"
    model = Award

    def __init__(self, instance=WILDCARD):
        super(AwardFilter, self).__init__(instance)

    def apply(self, queryset):
        if self.slug == WILDCARD:
            return queryset.exclude(awards__isnull=True)
        else:
            # return products that have won this specific award
            return queryset.filter(awards__award__slug=self.slug)

    def __unicode__(self):
        if self.slug == WILDCARD:
            return u'award winners'
        else:
            return self.get_name() + " award"


class BrandFilter(RelatedModelFilter):

    filter_key = "filterBrand"
    related_name = "brand"
    model = Brand

    def __unicode__(self):
        return self.get_name() + " brand"


class ThemeFilter(RelatedModelFilter):

    filter_key = "filterTheme"
    related_name = "themes"
    model = Theme

    def __unicode__(self):
        return self.get_name() + " theme"


class MaxPriceFilter(Filter):

    filter_key = "filterMaxPrice"

    def __init__(self, max_price):
        if not isinstance(max_price, Decimal):
            max_price = Decimal(max_price)
        self.max_price = max_price

    def apply(self, queryset):
        where_clause = "COALESCE(sale_price, price) <= " + str(self.max_price)
        return queryset.extra(where=[where_clause])

    def __unicode__(self):
        return "under " + currency(self.max_price)

    def value_for_url(self):
        return str(self.max_price)


class AgeRangeFilter(Filter):

    filter_key = "ageRange"

    def __init__(self, value=None, min_age=None, max_age=None):
        if value is not None:
            (min_age, max_age) = self.decode_value(value)

        if max_age and max_age < min_age:
            raise Exception("Max age must be larger than min age.")
        self.min_age = min_age
        self.max_age = max_age

    def apply(self, queryset):
        """
        Return all products that apply to children within the given age range.
        Given a certain age, n, a product applies to that age if n >= product.min_age and n <= product.max_age.
        Need to use an OR query
        """
        if self.max_age is None:
            # no maximum age limit, so we want all the toys with a min_age less than or equal to self.min_age and
            # a maximum age that is larger than or equal to self.min_age
            queryset = queryset.filter(Q(max_age=None) | Q(max_age__gte=self.min_age), min_age__lte=self.min_age)
        else:
            queryset = queryset.filter(Q(max_age=None) | Q(max_age__gte=self.min_age), min_age__lte=self.max_age)

        return queryset

    def value_for_url(self):
        return "%s+%s" % (self.min_age, self.max_age)

    def decode_value(self, value):
        """
        Decodes a string of format [num]+[num|None]
        """
        tokens = value.split('+')
        assert(len(tokens) == 2)
        last_token = None
        if tokens[1] != 'None':
            last_token = int(tokens[1])
        return int(tokens[0]), last_token

    def __unicode__(self):
        if self.min_age == 0 and self.max_age is None:
            return "all ages"
        if self.min_age and self.max_age is None:
            return "ages %d+" % self.min_age
        if self.min_age == 0 and self.max_age == 0:
            return "birth - 12 months"
        if self.min_age == 1 and self.max_age == 1:
            return "12 - 24 months"
        if self.min_age == self.max_age:
            return "age %s" % self.min_age
        return "ages %d - %d" % (self.min_age, self.max_age)


class ColorFilter(Filter):

    filter_key = "color"

    def __init__(self, name):
        self.name = name

    def apply(self, queryset):
        """
        Returns products that have the given color option.
        """
        # get a list of product instances with this color option
        try:
            option = Color.objects.get(name=self.name)
            return queryset.filter(instances__options=option)
        except Color.DoesNotExist:
            # bogus color, no products could possibly match
            return queryset.none()

    def value_for_url(self):
        return self.name

    def __unicode__(self):
        return self.name


class RecentlyAddedFilter(Filter):

    filter_key = "filterNew"

    def __init__(self, days):
        self.days = int(days)

    def apply(self, queryset):
        return queryset.filter(created_at__gte=(datetime.now() - timedelta(days=self.days)))

    def value_for_url(self):
        return str(self.days)

    def __unicode__(self):
        return "new within the last %d days" % self.days


class CountryOfOriginFilter(Filter):

    filter_key = "madeIn"

    def __init__(self, country_code):
        self.country_code = country_code

    def apply(self, queryset):
        return queryset.filter(country_of_origin=self.country_code)

    @property
    def country_name(self):
        return OFFICIAL_COUNTRIES.get(self.country_code, 'unknown').title()

    def __unicode__(self):
        return "made in %s" % self.country_name

    def value_for_url(self):
        return self.country_code


# manually register our filters
FILTERS = {
    AwardFilter.filter_key: AwardFilter,
    OnSaleFilter.filter_key: OnSaleFilter,
    IsBoxStufferFilter.filter_key: IsBoxStufferFilter,
    IsEcoFriendlyFilter.filter_key: IsEcoFriendlyFilter,
    BrandFilter.filter_key: BrandFilter,
    ThemeFilter.filter_key: ThemeFilter,
    MaxPriceFilter.filter_key: MaxPriceFilter,
    RecentlyAddedFilter.filter_key: RecentlyAddedFilter,
    AgeRangeFilter.filter_key: AgeRangeFilter,
    ColorFilter.filter_key: ColorFilter,
    CountryOfOriginFilter.filter_key: CountryOfOriginFilter,
}


def parse_filters(request):
    filters = []
    for filter_key, value in request.GET.items():
        if filter_key in FILTERS:
            filter_clazz = FILTERS[filter_key]
            try:
                filters.append(filter_clazz(unquote_plus(value)))
            except:
                # just ignore the filter, the value may be malformed
                pass
    return filters


def filter_products(request, queryset):
    filters = parse_filters(request)
    for a_filter in filters:
        queryset = a_filter.apply(queryset)
    return queryset, filters