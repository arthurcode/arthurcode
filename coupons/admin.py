from django.contrib import admin
from models import Discount

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'type', 'amount', 'start_date', 'end_date', 'is_active')

admin.site.register(Discount, DiscountAdmin)
