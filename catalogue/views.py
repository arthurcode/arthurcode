# Create your views here.
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from catalogue.models import Product, Category
from arthurcode import settings


def home_view(request):
    root_categories = Category.objects.root_nodes().filter(is_active=True).order_by('name')
    return render_to_response("home.html", locals(), context_instance=RequestContext(request))


def product_detail_view(request, slug=""):
    product = get_object_or_404(Product, slug=slug)
    breadcrumbs = product.category.get_ancestors(ascending=False, include_self=True)  # will always have at least one entry
    meta_description = product.short_description
    return render_to_response("product_detail.html", locals(), context_instance=RequestContext(request))


def category_view(request, category_slug=""):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        descendant_categories = category.get_descendants(include_self=True)
        products = Product.active.filter(category__in=descendant_categories)
        meta_description = category.description
        child_categories = add_product_count(category.get_children())
    else:
        category = None
        products = Product.active.all()
        meta_description = "All products for sale at %s." % settings.SITE_NAME
        child_categories = add_product_count(Category.objects.root_nodes())
    return render_to_response("category.html", locals(), context_instance=RequestContext(request))


def add_product_count(category_queryset):
    """
    Adds a 'product_count' attribute to the categories in the given queryset.  The count is cumulative over all
    of a category's subcategories.
    """
    return Category.objects.add_related_count(category_queryset, Product, 'category', 'product_count', cumulative=True)