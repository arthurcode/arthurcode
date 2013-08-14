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

    return {
        'option': option,
        'is_color': is_color,
        'is_size': is_size,
    }


@register.inclusion_tag('_product_option_field.html', takes_context=True)
def product_option_field(context, field):
    return {
        'field': field,
        'option_id_map': context['option_id_map']
    }
