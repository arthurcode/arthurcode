from django import template
from cart import cartutils

register = template.Library()


@register.inclusion_tag("_cart_summary.html")
def cart_summary(request):
    cart_item_count = cartutils.cart_distinct_item_count(request)
    return {'cart_item_count': cart_item_count}