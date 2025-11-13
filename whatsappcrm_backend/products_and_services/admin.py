from django.contrib import admin
from .models import Product, ProductCategory, ProductImage, SerializedItem

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for the ProductCategory model.
    """
    list_display = ('name', 'parent', 'description')
    search_fields = ('name', 'description')
    list_filter = ('parent',)
    ordering = ('name',)

class ProductImageInline(admin.TabularInline):
    """
    Inline admin descriptor for ProductImage model.
    This allows managing product images directly within the Product admin page.
    """
    model = ProductImage
    extra = 1  # Show one empty form for adding a new image by default
    fields = ('image', 'alt_text')
    readonly_fields = ('created_at',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for the Product model.
    """
    list_display = ('name', 'sku', 'product_type', 'category', 'price', 'is_active', 'stock_quantity', 'country_of_origin', 'brand')
    search_fields = ('name', 'sku', 'description', 'brand', 'barcode')
    list_filter = ('product_type', 'category', 'is_active', 'country_of_origin', 'brand')
    ordering = ('name',)
    inlines = [ProductImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'sku', 'description', 'product_type', 'category', 'brand')
        }),
        ('Pricing & Availability', {
            'fields': ('price', 'currency', 'is_active')
        }),
        ('Inventory & Origin', {
            'fields': ('stock_quantity', 'country_of_origin')
        }),
        ('Digital & External Links', {
            'fields': ('website_url', 'whatsapp_catalog_id')
        }),
        ('Software & Flow Specific', {
            'classes': ('collapse',),
            'fields': ('license_type', 'dedicated_flow_name')
        }),
        ('Relationships', {
            'classes': ('collapse',),
            'fields': ('parent_product', 'compatible_products', 'manufacturer')
        }),
    )

@admin.register(SerializedItem)
class SerializedItemAdmin(admin.ModelAdmin):
    """
    Admin interface for the SerializedItem model.
    """
    list_display = ('serial_number', 'product', 'status')
    search_fields = ('serial_number', 'product__name', 'barcode')
    list_filter = ('status', 'product__category')
    autocomplete_fields = ('product',)