# Create your views here.
from search.forms import SearchForm
from search import searchutils
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.views.decorators.http import require_POST
import urllib

@require_POST
def product_search_view(request):
    post_data = request.POST.copy()
    form = SearchForm(data=post_data)
    if form.is_valid():
        # save the search query in the database
        q = form.cleaned_data['q']
        category_slug = form.cleaned_data.get('category_slug', '')
        searchutils.store(request, q)
        return HttpResponseRedirect(reverse('catalogue_category', kwargs={'category_slug': category_slug})
                                    + "?" + urllib.urlencode({'search': q}))
    return HttpResponseRedirect(post_data['from'])
