"""
Contains filters for filtering catalogue queries.
"""
from django.db.models import Count
from catalogue.models import Award

WILDCARD = "any"


class Filter(object):

    def apply(self, queryset):
        return queryset

    def __unicode__(self):
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


class OnSaleFilter(Filter):

    filter_key = "filterOnSale"

    def __init__(self, on_sale=True):
        if isinstance(on_sale, (str, unicode)):
            on_sale = on_sale == 'True'
        self.on_sale = on_sale

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

FILTERS = {
    AwardFilter.filter_key: AwardFilter,
    OnSaleFilter.filter_key: OnSaleFilter,
}


def parse_filters(request):
    filters = []
    for filter_key, value in request.GET.items():
        if filter_key in FILTERS:
            filter_clazz = FILTERS[filter_key]
            filters.append(filter_clazz(value))
    return filters


def filter_products(request, queryset):
    filters = parse_filters(request)
    for a_filter in filters:
        queryset = a_filter.apply(queryset)
    return queryset, filters