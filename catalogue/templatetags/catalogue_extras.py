from django.template import Library
from catalogue.models import ProductOption

register = Library()

@register.inclusion_tag('_product_option.html', takes_context=True)
def product_option(context, option):
    """
    Outputs a div representing a product option.  This div is meant to be visual replacement for the ugly default
    radio button.
    """
    is_color = option.category == ProductOption.COLOR
    is_size = option.category == ProductOption.SIZE
    background_color = "white"
    if is_color:
        background_color = option.color.html
    text = ""
    if is_size:
        text = option.size.short_name

    return {
        'option': option,
        'is_color': is_color,
        'is_size': is_size,
        'background_color': background_color,
        'text': text,
    }


@register.inclusion_tag('_product_option_field.html', takes_context=True)
def product_option_field(context, field):
    return {
        'field': field,
        'option_id_map': context['option_id_map']
    }


@register.inclusion_tag('_thumbnail.html', takes_context=True)
def thumb(context, product):
    return {
        'product': product,
        'request': context.get('request', None)
    }


@register.inclusion_tag('_choose_filter.html', takes_context=True)
def choose_filter(context, filter):
    return {
        'filter': filter,
        'request': context.get('request', None)
    }
