from django.contrib.admin import ModelAdmin, site, TabularInline, StackedInline
from orders.models import Order, OrderItem, OrderBillingAddress, OrderShippingAddress


class OrderItemInline(TabularInline):
    model = OrderItem


class BillingAddressInline(StackedInline):
    model = OrderBillingAddress


class ShippingAddressInline(StackedInline):
    model = OrderShippingAddress

class OrderAdmin(ModelAdmin):
    list_display = ('__unicode__', 'date', 'status', 'total')
    inlines = [BillingAddressInline, ShippingAddressInline, OrderItemInline]
    readonly_fields = ('date', 'last_updated')


site.register(Order, OrderAdmin)