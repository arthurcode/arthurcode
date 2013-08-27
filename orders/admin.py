from django.contrib.admin import ModelAdmin, site, TabularInline, StackedInline
from orders.models import Order, OrderItem, OrderBillingAddress, OrderShippingAddress


class OrderItemInline(TabularInline):
    model = OrderItem


class BillingAddressInline(StackedInline):
    model = OrderBillingAddress


class ShippingAddressInline(StackedInline):
    model = OrderShippingAddress

class OrderAdmin(ModelAdmin):
    list_display = ('__unicode__', 'user', 'date', 'status', 'payment_status')
    inlines = [BillingAddressInline, ShippingAddressInline, OrderItemInline]
    readonly_fields = ('date', 'last_updated', 'shipping_charge', 'transaction_id', 'ip_address',
                       'merchandise_total', 'payment_status')

    fieldsets = (
        ('Order Status', {
            'fields': ('status', 'date', 'last_updated')
        }),
        ('Shipping', {
            'fields': ('is_pickup',)
        }),
        ('Payment Details', {
            'fields': ('payment_status', 'merchandise_total', 'shipping_charge', 'transaction_id',)
        }),
        ('Customer Info', {
            'classes': ('collapse',),
            'fields': ('user', 'email', 'phone', 'contact_method', 'ip_address')
        })
    )


site.register(Order, OrderAdmin)