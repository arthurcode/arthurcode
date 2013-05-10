from django import template
from cart import cartutils

register = template.Library()


@register.inclusion_tag("_order_summary.html")
def order_summary(order):
    cart_item_count = cartutils.cart_distinct_item_count(order.request)
    subtotal = cartutils.cart_subtotal(order.request)
    return {
        'item_count': cart_item_count,
        'subtotal': subtotal,
        'order': order,
    }
