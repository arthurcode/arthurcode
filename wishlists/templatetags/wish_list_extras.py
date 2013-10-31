from django import template
register = template.Library()

@register.filter
def in_cart(wish_list_item, request):
    return wish_list_item.in_cart(request)
