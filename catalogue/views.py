# Create your views here.
from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from catalogue.models import Product, Category


def home_view(request):
    root_categories = Category.objects.root_nodes().filter(is_active=True).order_by('name')
    return render_to_response("home.html", locals(), context_instance=RequestContext(request))


def product_detail_view(request, slug=""):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render_to_response("product_detail.html", locals(), context_instance=RequestContext(request))


def category_view(request, category_slug=""):
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
    else:
        category = None
    return render_to_response("category.html", locals(), context_instance=RequestContext(request))