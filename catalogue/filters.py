"""
Contains filters for filtering catalogue queries.
"""
from django.db.models import Count
from catalogue.models import Award, Brand, Theme
from utils.util import to_bool
from decimal import Decimal
from utils.templatetags.extras import currency
from django.db.models import Model
from datetime import datetime, timedelta

WILDCARD = "any"


class Filter(object):

    filter_key = None  # subclasses must define

    def apply(self, queryset):
        return queryset

    def __unicode__(self):
        raise Exception("Subclasses must override")

    def as_param(self):
        return self.filter_key + "=" + self.value_for_url()

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
            # return products that have won one or more awards
            return queryset.annotate(na=Count('awards')).filter(na__ge=1)
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