from django.template import Library
from catalogue.templatetags.catalogue_extras import thumb

register = Library()

@register.inclusion_tag('_review_it_thumbnail.html', takes_context=True)
def review_thumb(context, product):
    return thumb(context, product)
