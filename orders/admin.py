from django.contrib.admin import ModelAdmin, site, TabularInline, StackedInline
from orders.models import Order, OrderItem, OrderBillingAddress, OrderShippingAddress


class OrderItemInline(TabularInline):
    model = OrderItem


class BillingAddressInline(StackedInline):
    model = OrderBillingAddress


class ShippingAddressInline(StackedInline):
    model = OrderShippingAddress

class OrderAdmin(ModelAdmin):
    list_display = ('__unicode__', 'user', 'date', 'status')
    inlines = [BillingAddressInline, ShippingAddressInline, OrderItemInline]
    readonly_fields = ('date', 'last_updated', 'shipping_charge', 'ip_address',
                       'merchandise_total')

    fieldsets = (
        ('Order Status', {
            'fields': ('status', 'date', 'last_updated')
        }),
        ('Shipping', {
            'fields': ('is_pickup',)
        }),
        ('Payment Details', {
            'fields': ('merchandise_total', 'shipping_charge',)
        }),
        ('Customer Info', {
            'classes': ('collapse',),
            'fields': ('user', 'email', 'phone', 'contact_method', 'ip_address')
        })
    )


site.register(Order, OrderAdmin)