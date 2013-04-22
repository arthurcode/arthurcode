from django.contrib import admin
from accounts.models import CustomerProfile, CustomerBillingAddress, CustomerShippingAddress


class BillingAddressInline(admin.StackedInline):
    model = CustomerBillingAddress
    extra = 0


class ShippingAddressInline(admin.StackedInline):
    model = CustomerShippingAddress
    extra = 0


class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name',)
    inlines = [ShippingAddressInline, BillingAddressInline]

admin.site.register(CustomerProfile, CustomerProfileAdmin)