# Create your views here.
from django.shortcuts import get_object_or_404, render_to_response, redirect
from django.template import RequestContext
from catalogue.models import Product, Category, Brand, Theme
from arthurcode import settings
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from cart.forms import ProductAddToCartForm
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from cart import cartutils
from catalogue import filters
from django.db.models import Count, Sum

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
    if request.method == 'POST':
        # add to cart, create the bound form
        postdata = request.POST.copy()
        form = ProductAddToCartForm(request, postdata)
        # check if posted data is valid
        if form.is_valid():
            #add to cart and redirect to cart page
            cartutils.add_to_cart(request)
            # if test cookie worked, get rid of it
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            return HttpResponseRedirect(reverse('show_cart'))
    else:
        # it's a GET, create the unbound form.  Note request as a kwarg
        form = ProductAddToCartForm(request=request)
        # assign the hidden input the product slug
        form.fields['product_slug'].widget.attrs['value'] = slug
    # set the test cookie on our first GET request
    request.session.set_test_cookie()
    product = get_object_or_404(Product, slug=slug)
    breadcrumbs = product.category.get_ancestors(ascending=False, include_self=True)  # will always have at least one entry
    meta_description = product.short_description
    return render_to_response("product_detail.html", locals(), context_instance=RequestContext(request))


def category_view(request, category_slug=""):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        descendant_categories = category.get_descendants(include_self=True)
        product_list = Product.active.filter(category__in=descendant_categories)
        meta_description = category.description
        child_categories = category.get_children()
        parent_categories = category.get_ancestors(ascending=False, include_self=False)
    else:
        category = None
        parent_categories = None
        product_list = Product.active.all()
        meta_description = "All products for sale at %s." % settings.SITE_NAME
        child_categories = Category.objects.root_nodes()

    product_list, applied_filters = filters.filter_products(request, product_list)
    child_categories = child_categories.order_by('name')
    # only categories with > 0 products will be preserved in this list
    child_categories = add_product_count(child_categories, product_list)
    product_list, sort_key = _sort(request, product_list)

    # paginate the product listing
    pageSize = request.GET.get('pageSize') or DEFAULT_PAGE_SIZE

    showing_all_products = False
    if pageSize == "All":
        pageSize = max(product_list.count(), 1)
        showing_all_products = True

    # make sure pageSize is an integer.  If it isn't, fall back to the default size
    try:
        pageSize = int(pageSize)
        if pageSize < 1:
            pageSize = DEFAULT_PAGE_SIZE
    except:
        pageSize = DEFAULT_PAGE_SIZE
    paginator = Paginator(product_list, per_page=pageSize, allow_empty_first_page=True)
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
            ('rating', 'Rating'),
            ('new', 'Newest')
        ],
        'filters': applied_filters,
        'brands': get_brands(products),
        'themes': get_themes(products),
    }
    return render_to_response("category.html", context, context_instance=RequestContext(request))

PRODUCT_SORTS = {
    'bestselling': lambda q: q, # TODO
    # http://stackoverflow.com/questions/981375/using-a-django-custom-model-method-property-in-order-by
    'priceMin': lambda q: q.extra(
        select={"current_price": "COALESCE(sale_price, price)"},
        order_by=["current_price"]),
    'priceMax': lambda q: q.extra(
        select={"current_price": "COALESCE(sale_price, price)"},
        order_by=["-current_price"]),
    'nameA': lambda q: q.order_by('name'),
    'nameZ': lambda q: q.order_by('-name'),
    'rating': lambda q: q, #TODO
    'new': lambda q: q.order_by('-created_at'),
}


def _sort(request, queryset):
    """
    By default sort my bestselling products
    """
    sort_by = request.GET.get('sortBy', 'bestselling')
    sort_func = PRODUCT_SORTS['bestselling']
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


def get_brands(product_queryset):
    """
    Returns the set of brands that are linked to the products in the given queryset.  A product_count attribute will
    be annotated to each brand.  This works because the filter on products constrains the products that are included
    in product_count.  See https://docs.djangoproject.com/en/dev/topics/db/aggregation/ for more details.  Sweet!
    The brands will be in alphabetical order.
    """
    return Brand.objects.filter(products__in=product_queryset).annotate(product_count=Count('products')).order_by('name')


def get_themes(product_queryset):
    return Theme.objects.filter(products__in=product_queryset).annotate(product_count=Count('products')).order_by('name')