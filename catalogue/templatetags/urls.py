from utils.templatetags.extras import query_string, get_query_string
from django.template import Library
from django.core.urlresolvers import reverse

register = Library()

@register.inclusion_tag('_response.html', takes_context=True)
def add_filter(context, a_filter):
    """
    Adds the given filter to the catalogue query.
    All existing url params are preserved 'except' for 'page'.
    """
    to_add = a_filter.as_param()
    to_remove = "page"
    return query_string(context, to_add, to_remove)


@register.inclusion_tag('_response.html', takes_context=True)
def remove_filter(context, a_filter):
    """
    Removes the given filter from the catalogue query.
    All existing urls params are preserved except for the filter in question and 'page'.
    """
    to_add = ""
    to_remove = ",".join(["page", a_filter.filter_key])
    return query_string(context, to_add, to_remove)


@register.inclusion_tag('_response.html', takes_context=True)
def go_to_category(context, category):
    to_add = None
    to_remove = "page"
    params = dict(context['request'].GET.items())
    query_string = get_query_string(params, to_add, to_remove)
    url = reverse('catalogue_category', kwargs={'category_slug': category}) + query_string
    return {"response": url}

