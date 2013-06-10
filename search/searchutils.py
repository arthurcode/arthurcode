from search.models import SearchTerm
from catalogue.models import Product
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


def products(search_text, products=Product.active.all()):
    """
    Search for products matching the given search text.  By default all active products are queried, but this can be
    modified by passing a custom 'products' queryset.
    """
    words = _prepare_words(search_text)

    for word in words:
        products = products.filter(Q(name__icontains=word) |
                                    Q(short_description__icontains=word) |
                                    Q(long_description__icontains=word) |
                                    Q(upc__iexact=word) |                   # TODO include sku when I have a sku
                                    Q(brand__name__icontains=word) |
                                    Q(themes__name__icontains=word))
    return products


def _prepare_words(search_text):
    """
    Strip out common words, limit to 5 words
    """
    words = search_text.split()
    for common in STRIP_WORDS:
        if common in words:
            words.remove(common)
    return words[0:5]