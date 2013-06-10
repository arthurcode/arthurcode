from search.models import SearchTerm
from catalogue.models import Product, Category
from django.db.models import Q

STRIP_WORDS = ['a', 'an', 'and', 'by', 'for', 'from', 'in', 'no', 'not', 'of', 'on', 'or', 'that', 'the', 'to', 'with']


def store(request, q):
    """
     Store the search text in the database
    """
    if len(q) > 2:
        term = SearchTerm()
        term.q = q
        term.ip_address = request.META.get('REMOTE_ADDR')
        term.user = None
        if request.user.is_authenticated():
            term.user = request.user
        term.save()


def categories(search_text, categories=None):
    words = _prepare_words(search_text)
    return _categories(words, categories)


def _categories(search_words, categories=None):
    if not categories:
        categories = Category.objects.filter(is_active=True)
    for word in search_words:
        categories = categories.filter(Q(name__icontains=word) |
                                       Q(description__icontains=word))
    return categories


def products(search_text, products=Product.active.all()):
    """
    Search for products matching the given search text.  By default all active products are queried, but this can be
    modified by passing a custom 'products' queryset.
    """
    words = _prepare_words(search_text)
    product_query = Q()

    # for a product to match every word needs to appear in at least one of the following fields
    for word in words:
        product_query &= (Q(name__icontains=word) |
                          Q(short_description__icontains=word) |
                          Q(long_description__icontains=word) |
                          Q(upc__iexact=word) |                   # TODO include sku when I have a sku
                          Q(brand__name__icontains=word) |
                          Q(themes__name__icontains=word))

    # factor in category matches
    categories = _categories(words)
    category_query = Q()

    # to get a category match the product needs to appear in at least one of the matching categories
    for category in categories:
        category_query |= Q(category__in=category.get_leafnodes(include_self=True))

    # return products that either match on the product query or the catalogue query
    return products.filter(Q(product_query | category_query)).distinct()


def _prepare_words(search_text):
    """
    Strip out common words, limit to 5 words
    """
    words = search_text.split()
    for common in STRIP_WORDS:
        if common in words:
            words.remove(common)
    return words[0:5]