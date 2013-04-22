from django.contrib import admin
from accounts.models import CustomerProfile, CustomerBillingAddress, CustomerShippingAddress


class BillingAddressInline(admin.StackedInline):
    model = CustomerBillingAddress
    extra = 0
    readonly_fields = ('last_used',)


class ShippingAddressInline(admin.StackedInline):
    model = CustomerShippingAddress
    extra = 0
    readonly_fields = ('last_used',)


class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'last_name', 'first_name', 'date_added')
    inlines = [ShippingAddressInline, BillingAddressInline]
    readonly_fields = ('date_added',)

admin.site.register(CustomerProfile, CustomerProfileAdmin)