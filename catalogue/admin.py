from django.contrib import admin
from django import forms
from catalogue.models import Product, Category, Award, AwardInstance, Brand, Theme, ProductImage, ProductInstance, \
    Color, Size, Specification, Dimension
from mptt.admin import MPTTModelAdmin


class AwardAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']

admin.site.register(Award, AwardAdmin)


class AwardInstanceAdmin(admin.ModelAdmin):
    pass

admin.site.register(AwardInstance, AwardInstanceAdmin)


class BrandAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Brand, BrandAdmin)


class ThemeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Theme, ThemeAdmin)


class ProductImageInline(admin.TabularInline):
    model = ProductImage


class ProductSpecificationInline(admin.TabularInline):
    model = Specification


class ProductDimensionInline(admin.TabularInline):
    model = Dimension

class ProductAdminForm(forms.ModelForm):
    short_description = forms.CharField(widget=forms.Textarea)
    meta_description = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Product


class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [
        ProductDimensionInline, ProductSpecificationInline, ProductImageInline
    ]

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'brand', 'country_of_origin', 'is_active', 'min_age', 'max_age', 'created_at', 'updated_at')
        }),
        ('Pricing', {
            'fields': ('price', 'sale_price')
        }),
        ('Description', {
            'fields': ('meta_description', 'short_description', 'long_description')
        }),
        ('Features', {
            'fields': ('is_bestseller', 'is_featured', 'is_box_stuffer', 'is_green')
        }),
        ('Awards', {
            'fields': ('awards',)
        }),
        ('Themes', {
            'fields': ('themes',)
        }),
        ('Dimensions', {
            'fields': ('weight',)
        })
    )

    list_display = ('name', 'category', 'price', 'sale_price', 'created_at', 'updated_at', 'is_award_winner')
    list_display_links = ('name', 'category')
    list_per_page = 50
    ordering = ['-created_at']
    search_fields = ['name', 'description', 'meta_keywords', 'meta_description']
    readonly_fields = ('created_at', 'updated_at', 'is_award_winner')

    # sets up slug to be generated from product name
    prepopulated_fields = {'slug': ('name',)}


# registers your product model with the admin site
admin.site.register(Product, ProductAdmin)


class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'product_count', 'created_at', 'updated_at',)
    list_display_links = ('name',)
    search_fields = ['name', 'description']
    readonly_fields = ('created_at', 'updated_at',)

    # sets up slug to be generated from category name
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category, CategoryAdmin)


class ColorProductOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'html')

admin.site.register(Color, ColorProductOptionAdmin)


class SizeProductOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'sort_index')
    ordering = ('sort_index', 'name')

admin.site.register(Size, SizeProductOptionAdmin)

class ProductInstanceAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'quantity', 'sku')
    search_fields = ('sku', 'product__name')

admin.site.register(ProductInstance, ProductInstanceAdmin)
