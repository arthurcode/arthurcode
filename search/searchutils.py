from search.models import SearchTerm


def store(request, q, hits):
    """
     Store the search text in the database
    """
    if len(q) > 1:
        term = SearchTerm()
        term.q = q
        term.ip_address = request.META.get('REMOTE_ADDR')
        term.user = None
        term.hits = hits
        if request.user.is_authenticated():
            term.user = request.user
        term.full_clean()
        term.save()