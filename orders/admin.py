from django.contrib.admin import ModelAdmin, site, TabularInline
from orders.models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem


class OrderAdmin(ModelAdmin):
    list_display = ('__unicode__', 'date', 'status', 'total')
    inlines = [OrderItemInline,]
    readonly_fields = ('date', 'last_updated')


site.register(Order, OrderAdmin)