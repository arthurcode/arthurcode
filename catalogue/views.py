from decimal import Decimal

from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db.models import Count, Sum, Avg

from catalogue.models import Product, Category, Brand, Theme, ProductInstance, ProductOption, \
    Award
from arthurcode import settings
from cart.forms import ProductAddToCartForm
from catalogue import filters
from search import searchutils
import json
from catalogue.forms import RestockNotifyForm


DEFAULT_PAGE_SIZE = 16


def home_view(request):
    return redirect('catalogue_featured')


def featured_view(request):
    featured_products = Product.active.filter(is_featured=True)
    context = {
        'featured_products': featured_products
    }
    return render_to_response("featured.html", context, context_instance=RequestContext(request))


def product_detail_view(request, slug=""):
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        # add to cart, create the bound form
        postdata = request.POST.copy()
        form = ProductAddToCartForm(product, request, postdata)
        # check if posted data is valid
        if form.is_valid():
            #add to cart and redirect to cart page
            form.save()
            # if test cookie worked, get rid of it
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponseRedirect(reverse('show_cart'))
    else:
        # it's a GET, create the unbound form.  Note request as a kwarg
        form = ProductAddToCartForm(product, request=request)
    # set the test cookie on our first GET request
    request.session.set_test_cookie()
    breadcrumbs = product.get_breadcrumbs()
    meta_description = product.meta_description
    reviews = product.reviews.select_related('product', 'user__public_profile').\
        prefetch_related('flags').order_by('-last_modified')
    images = product.images.order_by('-is_primary')           # make sure the primary image(s) appear first in this list

    # map from product-option-id --> product-image-id
    option_to_image_map = {}
    for image in images:
        if image.option:
            option_to_image_map[image.option.id] = image.id

    product_options = product.get_options()
    # map from option-id (string) --> option instance
    option_id_map = {}
    for options in product_options.values():
        for option in options:
            option_id_map[str(option.id)] = option

    # map from option-id tupple --> stock counts, use this data to indicate out-of-stockiness for product options
    option_to_stock_map = {}
    for product_instance in product.instances.all():
        options = product_instance.options.all()
        # first go through and accumulate all of the option id singles
        for o in options:
            k = str(o.id)
            if k in option_to_stock_map:
                option_to_stock_map[k] += product_instance.quantity
            else:
                option_to_stock_map[k] = product_instance.quantity

        if options.count() > 2:
            raise Exception("Can't handle products with more than two options, yet.")
        elif options.count() == 2:
            k = "%d,%d" % (options[0].id, options[1].id)
            option_to_stock_map[k] = product_instance.quantity
            k = "%d,%d" % (options[1].id, options[0].id)
            option_to_stock_map[k] = product_instance.quantity

    option_to_stock_map = json.dumps(option_to_stock_map)  # should now be a string

    # manually calculate the average rating rather than hit the DB again
    avg = None
    if reviews:
        avg = Decimal('0')
        for review in reviews:
            avg += review.rating
        avg /= reviews.count()

    context = {
        'form': form,
        'product': product,
        'breadcrumbs': list(breadcrumbs),                      # force evaluation to save a query in the template
        'meta_description': meta_description,
        'reviews': reviews,
        'avg_rating': avg,
        'images': images,
        'option_id_map': option_id_map,
        'option_to_stock_map': option_to_stock_map,
        'option_to_image_map': json.dumps(option_to_image_map),  # now a json string
    }

    return render_to_response("product_detail.html", context, context_instance=RequestContext(request))


def category_view(request, category_slug=""):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        descendant_categories = category.get_descendants(include_self=True)
        pre_filter_product_list = Product.active.filter(category__in=descendant_categories)
        meta_description = category.description
        child_categories = category.get_children()
        parent_categories = category.get_ancestors(ascending=False, include_self=False)
    else:
        category = None
        parent_categories = None
        pre_filter_product_list = Product.active.all()
        meta_description = "All products for sale at %s." % settings.SITE_NAME
        child_categories = Category.objects.root_nodes()

    # implement a product search
    search_text = request.GET.get('search', None)
    if search_text:
        # always do the search before the filtering
        pre_filter_product_list = searchutils.products(search_text, pre_filter_product_list)
         # force the evaluation of the pre-filter product list queryset to
        # avoid running expensive search sub-queries more than once
        pre_filter_product_list = Product.objects.filter(id__in=[p.id for p in pre_filter_product_list])

    final_product_list, applied_filters = filters.filter_products(request, pre_filter_product_list)
    final_product_list = final_product_list.annotate(rating=Avg('reviews__rating'))
    final_product_list, sort_key = _sort(request, final_product_list)
    child_categories = child_categories.order_by('name')

    # get a finalized list of products in the form of a subquery.  This also forces the final_product_list queryset
    # to be evaluated which is fine, it would be evaluated in the template regardless.
    final_product_subquery = Product.objects.filter(id__in=[p.id for p in final_product_list])

    # only categories with > 0 products will be preserved in this list
    child_categories = add_product_count(child_categories, final_product_subquery)

    # paginate the product listing
    pageSize = request.GET.get('pageSize') or DEFAULT_PAGE_SIZE

    showing_all_products = False
    if pageSize == "All":
        pageSize = max(final_product_list.count(), 1)
        showing_all_products = True

    # make sure pageSize is an integer.  If it isn't, fall back to the default size
    try:
        pageSize = int(pageSize)
        if pageSize < 1:
            pageSize = DEFAULT_PAGE_SIZE
    except:
        pageSize = DEFAULT_PAGE_SIZE
    paginator = Paginator(final_product_list, per_page=pageSize, allow_empty_first_page=True)
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator._num_pages)

    context = {
        'page_sizes': [DEFAULT_PAGE_SIZE, 32, 64, 96],
        'products': products,
        'showing_all_products': showing_all_products,
        'category': category,
        'parent_categories': parent_categories,
        'meta_description': meta_description,
        'child_categories': child_categories,
        'sort_key': sort_key,
        'sorts': [
            ('bestselling', 'Bestselling'),
            ('priceMin', 'Price (Low to high)'),
            ('priceMax', 'Price (High to Low)'),
            ('nameA', 'Name (A to Z)'),
            ('nameZ', 'Name (Z to A)'),
            ('rating', 'Top Rated'),
            ('new', 'Recently Added')
        ],
        'search_text': search_text,
        'filters': applied_filters,
        'brands': get_brands(pre_filter_product_list, final_product_subquery, applied_filters),
        'themes': get_themes(pre_filter_product_list, final_product_subquery, applied_filters),
        'prices': get_prices(pre_filter_product_list, final_product_subquery, applied_filters),
        'ages': get_ages(pre_filter_product_list, final_product_subquery, applied_filters),
        'features': get_features(final_product_subquery, applied_filters),
        'colors': get_colors(pre_filter_product_list, final_product_subquery, applied_filters),
        'countries': get_countries(pre_filter_product_list, final_product_subquery, applied_filters),
    }
    return render_to_response("category.html", context, context_instance=RequestContext(request))


PRODUCT_SORTS = {
    'bestselling': lambda q: q, # TODO
    # http://stackoverflow.com/questions/981375/using-a-django-custom-model-method-property-in-order-by
    'priceMin': lambda q: Product.select_current_price(q).order_by("current_price"),
    'priceMax': lambda q: Product.select_current_price(q).order_by("-current_price"),
    'nameA': lambda q: q.order_by('name'),
    'nameZ': lambda q: q.order_by('-name'),
    'rating': lambda q: q.order_by('-rating'),  # TODO: this puts NULLS FIRST, need to figure out a way around this
    'new': lambda q: q.order_by('-created_at'),
}


def _sort(request, queryset):
    """
    By default sort my bestselling products
    """
    sort_by = request.GET.get('sortBy', 'priceMax')
    sort_func = PRODUCT_SORTS['priceMax']
    if sort_by in PRODUCT_SORTS:
        sort_func = PRODUCT_SORTS[sort_by]
    return sort_func(queryset), sort_by


def add_product_count(category_queryset, product_queryset):
    """
    Returns the category queryset augmented with the number of matching products that fall within that category.  ATM
    this is done with several DB calls.  THIS NEEDS TO BE IMPROVED!
    Categories with zero matching products will be removed from the list.
    """
    categories = []
    for category in category_queryset:
        num_products = category.get_leafnodes(include_self=True).filter(product__in=product_queryset).annotate(product_count=Count('product')).aggregate(Sum('product_count'))['product_count__sum']
        if num_products > 0:
            setattr(category, 'product_count', num_products)
            categories.append(category)
    return categories


def get_brands(pre_filter_queryset, final_queryset, request_filters):
    """
    Returns the set of brands that are linked to the products in the given queryset.  A product_count attribute will
    be annotated to each brand.  This works because the filter on products constrains the products that are included
    in product_count.  See https://docs.djangoproject.com/en/dev/topics/db/aggregation/ for more details.  Sweet!
    The brands will be in alphabetical order.
    """
    queryset = pre_filter_queryset
    active_filter = None

    for a_filter in request_filters:
        if isinstance(a_filter, filters.BrandFilter):
            active_filter = a_filter
            continue
        queryset = a_filter.apply(queryset)

    if not active_filter:
        # there are no brand filters active, therefore we can go ahead and use final_queryset to simplify the subquery
        queryset = final_queryset

    brands = Brand.objects.filter(products__in=queryset).annotate(product_count=Count('products')).order_by('name')
    brand_filters = []

    for brand in brands:
        brand_filter = filters.BrandFilter(brand)
        is_active = active_filter and active_filter.slug == brand.slug
        # set the name to avoid a DB call in the template
        if is_active:
            active_filter.name = brand.name
        setattr(brand_filter, 'active_filter', is_active)
        setattr(brand_filter, 'product_count', brand.product_count)
        brand_filters.append(brand_filter)
    return brand_filters


def get_themes(pre_filter_queryset, final_queryset, request_filters):
    queryset = pre_filter_queryset
    active_filter = None

    for a_filter in request_filters:
        if isinstance(a_filter, filters.ThemeFilter):
            active_filter = a_filter
            continue
        queryset = a_filter.apply(queryset)

    if not active_filter:
        # there are no theme filters active, therefore we can go ahead and use final_queryset and simplify the subquery
        queryset = final_queryset

    themes = Theme.objects.filter(products__in=queryset).annotate(product_count=Count('products')).order_by('name')
    theme_filters = []

    for theme in themes:
        theme_filter = filters.ThemeFilter(theme)
        is_active = active_filter and active_filter.slug == theme.slug
        # set the name to avoid a DB call in the template
        if is_active:
            active_filter.name = theme.name
        setattr(theme_filter, 'active_filter', is_active)
        setattr(theme_filter, 'product_count', theme.product_count)
        theme_filters.append(theme_filter)
    return theme_filters


def get_prices(pre_filter_queryset, final_queryset, request_filters):
    """
    Returns a list of price bins for this queryset.  Bins without any counts will be removed.
    This hits the DB multiple times.  It should be possible to do this in a single query, but not without using
    custom SQL.  This is TBD.
    """
    price_bins = ('10', '20', '30', '40', '50', '75', '100', '200')
    price_filters = []
    queryset = pre_filter_queryset
    active_filter = None

    for a_filter in request_filters:
        if isinstance(a_filter, filters.MaxPriceFilter):
            active_filter = a_filter
            continue
        queryset = a_filter.apply(queryset)

    if not active_filter:
        # simplify the subquery when there is no currently active price filter
        queryset = final_queryset

    select = {}
    fields = []
    for price in price_bins:
        field = "lt" + price
        select[field] = "sum(case when COALESCE(sale_price, price) <= " + price + " then 1 else 0 end)"
        fields.append(field)

    breakdown = queryset.extra(select=select).values(*fields)
    if not breakdown: return []
    breakdown = breakdown[0]

    last_count = 0

    for price in price_bins:
        price_filter = filters.MaxPriceFilter(price)
        count = breakdown["lt" + price]
        is_active = active_filter and active_filter.max_price == price_filter.max_price
        if is_active or count > last_count:
            setattr(price_filter, 'active_filter', is_active)
            setattr(price_filter, 'product_count', count)
            price_filters.append(price_filter)
            last_count = count
    price_filters.reverse()
    return price_filters


def get_ages(pre_filter_queryset, final_queryset, request_filters):
    queryset = pre_filter_queryset
    active_filter = None

    for a_filter in request_filters:
        if isinstance(a_filter, filters.AgeRangeFilter):
            active_filter = a_filter
            continue
        queryset = a_filter.apply(queryset)

    if not active_filter:
        # simplification
        queryset = final_queryset

    age_bins = [(0, 0), (1, 1), (2, 2), (3, 4), (5, 7), (8, 11), (12, 14), (15, None)]  # age ranges copied from ToysRUs
    age_filters = []

    select = {}
    fields = []
    index = 0
    for min_age, max_age in age_bins:
        field = "bin%s" % index
        if max_age is None:
            params = (min_age, min_age)
        else:
            params = (max_age, min_age)
        select[field] = "sum(case when (min_age <= %d AND (max_age IS NULL OR max_age >= %d)) then 1 else 0 end)" % params
        fields.append(field)
        index += 1

    breakdown = queryset.extra(select=select).values(*fields)
    if not breakdown: return []
    breakdown = breakdown[0]

    index = 0
    for min_age, max_age in age_bins:
        age_filter = filters.AgeRangeFilter(min_age=min_age, max_age=max_age)
        is_active = active_filter and active_filter.min_age == min_age and active_filter.max_age == max_age
        count = breakdown["bin%s" % index]
        setattr(age_filter, 'active_filter', is_active)
        setattr(age_filter, 'product_count', count)
        if count > 0 or is_active:
            age_filters.append(age_filter)
        index += 1

    return age_filters


def get_colors(pre_filter_queryset, final_queryset, request_filters):
    queryset = pre_filter_queryset
    active_filter = None

    for a_filter in request_filters:
        if isinstance(a_filter, filters.ColorFilter):
            active_filter = a_filter
            continue
        queryset = a_filter.apply(queryset)

    if not active_filter:
        # simplification
        queryset = final_queryset

    options = queryset.filter(instances__options__category=ProductOption.COLOR).values('instances__options__name', 'instances__options__color__html').annotate(ocount=Count('instances__options__name'))
    color_filters = []

    for option_set in options:
        option_name = option_set['instances__options__name']
        if option_name is None:
            continue
        count = option_set['ocount']
        is_active = active_filter and active_filter.name == option_name
        if count or is_active:
            filter = filters.ColorFilter(option_name)
            setattr(filter, 'active_filter', is_active)
            setattr(filter, 'product_count', count)
            setattr(filter, 'html', option_set['instances__options__color__html'])
            color_filters.append(filter)

    return color_filters


def get_countries(pre_filter_queryset, final_queryset, request_filters):
    queryset = pre_filter_queryset
    active_filter = None

    for a_filter in request_filters:
        if isinstance(a_filter, filters.CountryOfOriginFilter):
            active_filter = a_filter
            continue
        queryset = a_filter.apply(queryset)

    if not active_filter:
        # simplification
        queryset = final_queryset

    countries_of_interest = ['CA', 'US']
    countries = queryset.filter(country_of_origin__in=countries_of_interest).values('country_of_origin').annotate(ccount=Count('id'))
    country_filters = []

    for country_set in countries:
        country = country_set['country_of_origin']
        count = country_set['ccount']
        filter = filters.CountryOfOriginFilter(country)
        is_active = active_filter and active_filter.country_code == country
        if is_active or count:
            setattr(filter, 'product_count', count)
            setattr(filter, 'active_filter', is_active)
            country_filters.append(filter)
    return country_filters


def get_features(product_queryset, applied_filters):
    """
    Returns the feature filters that apply to this product set.  A feature filter applies to the product set
    if it is currently-active or if it's associated product_count is greater than zero.
    """
    feature_filters = [filters.IsEcoFriendlyFilter(),
                       filters.AwardFilter(),
                       filters.OnSaleFilter(),
                       filters.IsBoxStufferFilter()]

    applied_filter_types = tuple([type(f) for f in applied_filters])

    for f in feature_filters:
        setattr(f, 'active_filter', isinstance(f, applied_filter_types))
        setattr(f, 'product_count', f.apply(product_queryset).count())
    return [f for f in feature_filters if f.product_count > 0 or f.active_filter]


def restock_notify_view(request, instance_id):
    """
    The customer can sign up to be notified via-email when this product instance comes back into stock.
    """
    instance = get_object_or_404(ProductInstance, id=instance_id)
    if request.method == "POST":
        data = request.POST.copy()
        data['instance_id'] = instance_id
        form = RestockNotifyForm(data=data)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(instance.get_absolute_url())
    else:
        # pre-fill with the logged-in user's email address if it is available
        email = request.user.email
        initial = {}
        if email:
            initial['email'] = email
        form = RestockNotifyForm(initial=initial)

    context = {
        'product': instance,
        'form': form,
    }
    return render_to_response('restock_notify.html', context, context_instance=RequestContext(request))


def brands_view(request):
    # only show brands with active products, display in alphabetical order
    brands = Brand.objects.filter(products__is_active=True).distinct().order_by('name')
    context = {
        'brands': brands,
    }
    return render_to_response('brands.html', context, context_instance=RequestContext(request))


def brand_view(request, brand_slug):
    brand = get_object_or_404(Brand, slug=brand_slug)
    filter = filters.BrandFilter(brand_slug)
    sort_func = PRODUCT_SORTS['bestselling']
    bestsellers = sort_func(filter.apply(Product.active.all()))[:5]

    context = {
        'brand': brand,
        'filter': filter,
        'bestsellers': bestsellers,
    }
    return render_to_response('brand.html', context, context_instance=RequestContext(request))


def awards_view(request):
    # get all awards that have been won by active products
    awards = Award.objects.filter(instances__products__is_active=True).distinct().order_by('name')
    context = {
        'awards': awards,
    }
    return render_to_response('awards.html', context, context_instance=RequestContext(request))


def award_view(request, award_slug):
    award = get_object_or_404(Award, slug=award_slug)
    filter = filters.AwardFilter(award_slug)
    sort_func = PRODUCT_SORTS['bestselling']
    bestsellers = sort_func(filter.apply(Product.active.all()))[:5]

    context = {
        'award': award,
        'filter': filter,
        'bestsellers': bestsellers,
    }
    return render_to_response('award.html', context, context_instance=RequestContext(request))
