"""
Contains filters for filtering catalogue queries.
"""
from django.db.models import Count
from catalogue.models import Award, Brand, Theme
from utils.util import to_bool
from decimal import Decimal
from utils.templatetags.extras import currency

WILDCARD = "any"


class Filter(object):

    filter_key = None # subclasses must define

    def apply(self, queryset):
        return queryset

    def __unicode__(self):
        raise Exception("Subclasses must override")

    def as_param(self):
        return self.filter_key + "=" + self.value_for_url()

    def value_for_url(self):
        raise Exception("Subclasses must override")

class AwardFilter(Filter):

    filter_key = "filterAward"

    def __init__(self, award_slug=WILDCARD):
        self.award_slug = award_slug

    def apply(self, queryset):
        if self.award_slug == WILDCARD:
            # return products that have won one or more awards
            return queryset.annotate(na=Count('awards')).filter(na__ge=1)
        else:
            # return products that have won this specific award
            return queryset.filter(awards__award__slug=self.award_slug)

    def __unicode__(self):
        if self.award_slug == WILDCARD:
            return u'award winners'
        else:
            award = Award.objects.filter(slug=self.award_slug)
            if award.count() > 0:
                return u'award = %s' % award[0].name
            else:
                return u'award = %s' % self.award_slug

    def value_for_url(self):
        return self.award_slug


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


class BrandFilter(Filter):

    filter_key = "filterBrand"

    def __init__(self, brand_slug):
        if isinstance(brand_slug, Brand):
            self.brand_slug = brand_slug.slug
            self.name = brand_slug.name
        else:
            self.brand_slug = brand_slug

    def apply(self, queryset):
        return queryset.filter(brand__slug=self.brand_slug)

    def __unicode__(self):
        return self.get_name() + " brand"

    def value_for_url(self):
        return self.brand_slug

    def get_name(self):
        if not hasattr(self, 'name'):
            brand = Brand.objects.filter(slug=self.brand_slug)
            if brand.count() > 0:
                self.name = brand[0].name
            else:
                self.name = self.brand_slug
        return self.name


class ThemeFilter(Filter):

    filter_key = "filterTheme"

    def __init__(self, theme_slug):
        if isinstance(theme_slug, Theme):
            self.theme_slug = theme_slug.slug
            self.name = theme_slug.name
        else:
            self.theme_slug = theme_slug

    def apply(self, queryset):
        return queryset.filter(themes__slug=self.theme_slug)

    def __unicode__(self):
        return self.get_name() + " theme"

    def value_for_url(self):
        return self.theme_slug

    def get_name(self):
        if not hasattr(self, 'name'):
            theme = Theme.objects.filter(slug=self.theme_slug)
            if theme.count() > 0:
                self.name = theme[0].name
            else:
                self.name = self.theme_slug
        return self.name


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


# manually register our filters
FILTERS = {
    AwardFilter.filter_key: AwardFilter,
    OnSaleFilter.filter_key: OnSaleFilter,
    IsBoxStufferFilter.filter_key: IsBoxStufferFilter,
    IsEcoFriendlyFilter.filter_key: IsEcoFriendlyFilter,
    BrandFilter.filter_key: BrandFilter,
    ThemeFilter.filter_key: ThemeFilter,
    MaxPriceFilter.filter_key: MaxPriceFilter,
}


def parse_filters(request):
    filters = []
    for filter_key, value in request.GET.items():
        if filter_key in FILTERS:
            filter_clazz = FILTERS[filter_key]
            try:
                filters.append(filter_clazz(value))
            except:
                # just ignore the filter, the value may be malformed
                pass
    return filters


def filter_products(request, queryset):
    filters = parse_filters(request)
    for a_filter in filters:
        queryset = a_filter.apply(queryset)
    return queryset, filters