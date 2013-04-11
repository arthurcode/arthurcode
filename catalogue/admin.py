from django.contrib import admin
from catalogue.models import Product, Category
from mptt.admin import MPTTModelAdmin


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'sale_price', 'created_at', 'updated_at',)
    list_display_links = ('name', 'category')
    list_per_page = 50
    ordering = ['-created_at']
    search_fields = ['name', 'description', 'meta_keywords', 'meta_description']
    readonly_fields = ('created_at', 'updated_at',)

    # sets up slug to be generated from product name
    prepopulated_fields = {'slug': ('name',)}


# registers your product model with the admin site
admin.site.register(Product, ProductAdmin)


class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'is_active', 'product_count', 'created_at', 'updated_at',)
    list_display_links = ('name',)
    search_fields = ['name', 'description']
    readonly_fields = ('created_at', 'updated_at',)

    # sets up slug to be generated from category name
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category, CategoryAdmin)
