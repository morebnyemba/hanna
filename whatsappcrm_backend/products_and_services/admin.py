from django.contrib import admin
from .models import Product, ProductCategory, SerializedItem

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for the ProductCategory model.
    """
    list_display = ('name', 'parent', 'description')
    search_fields = ('name', 'description')
    list_filter = ('parent',)
    ordering = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for the Product model.
    """
    list_display = ('name', 'sku', 'product_type', 'category', 'price', 'is_active')
    search_fields = ('name', 'sku', 'description')
    list_filter = ('product_type', 'category', 'is_active')
    ordering = ('name',)

@admin.register(SerializedItem)
class SerializedItemAdmin(admin.ModelAdmin):
    """
    Admin interface for the SerializedItem model.
    """
    list_display = ('serial_number', 'product', 'status')
    search_fields = ('serial_number', 'product__name')
    list_filter = ('status', 'product__category')
    autocomplete_fields = ('product',)