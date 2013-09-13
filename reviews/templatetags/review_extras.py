from django.template import Library

register = Library()

@register.inclusion_tag('_review_it_thumbnail.html', takes_context=True)
def review_thumb(context, product):
    return {
        'product': product,
        'request': context.get('request', None)
    }
