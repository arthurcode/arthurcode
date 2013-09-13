from django.template import Library

register = Library()

@register.inclusion_tag('_order.html', takes_context=True)
def order(context, order):
    return {
        'order': order,
    }