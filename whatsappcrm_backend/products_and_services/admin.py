from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductCategory, ProductImage, SerializedItem, Cart, CartItem

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
    list_display = ('name', 'sku', 'barcode', 'product_type', 'category', 'price', 'is_active', 'stock_quantity', 'meta_sync_status', 'country_of_origin', 'brand')
    search_fields = ('name', 'sku', 'barcode', 'description', 'brand')
    list_filter = ('product_type', 'category', 'is_active', 'country_of_origin', 'brand')
    ordering = ('name',)
    inlines = [ProductImageInline]
    actions = ['reset_meta_sync_attempts']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'sku', 'barcode', 'description', 'product_type', 'category', 'brand')
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
        ('Meta Catalog Sync Status', {
            'fields': ('meta_sync_attempts', 'meta_sync_last_error', 'meta_sync_last_attempt', 'meta_sync_last_success'),
            'classes': ('collapse',),
            'description': 'Track synchronization status with Meta (Facebook) Product Catalog'
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
    
    readonly_fields = ('meta_sync_attempts', 'meta_sync_last_error', 'meta_sync_last_attempt', 'meta_sync_last_success')
    
    def meta_sync_status(self, obj):
        """Display Meta sync status with color coding"""
        if obj.whatsapp_catalog_id:
            if obj.meta_sync_last_success:
                return format_html(
                    '<span style="color: green;">✓ Synced</span>'
                )
            else:
                return format_html(
                    '<span style="color: orange;">⚠ ID exists but never synced</span>'
                )
        elif obj.meta_sync_attempts >= 5:
            return format_html(
                '<span style="color: red;">✗ Failed (max attempts)</span>'
            )
        elif obj.meta_sync_attempts > 0:
            return format_html(
                '<span style="color: orange;">⚠ Retry pending ({}/5)</span>',
                obj.meta_sync_attempts
            )
        else:
            return format_html(
                '<span style="color: gray;">○ Not synced</span>'
            )
    meta_sync_status.short_description = 'Meta Sync Status'
    
    @admin.action(description='Reset Meta sync attempts (allows retry)')
    def reset_meta_sync_attempts(self, request, queryset):
        """Reset sync attempt counters for selected products"""
        count = queryset.update(
            meta_sync_attempts=0,
            meta_sync_last_error=None
        )
        self.message_user(
            request,
            f'Reset sync attempts for {count} product(s). They will be synced on next save.'
        )

@admin.register(SerializedItem)
class SerializedItemAdmin(admin.ModelAdmin):
    """
    Admin interface for the SerializedItem model.
    """
    list_display = ('serial_number', 'barcode', 'product', 'status')
    search_fields = ('serial_number', 'barcode', 'product__name')
    list_filter = ('status', 'product__category')
    autocomplete_fields = ('product',)
    fieldsets = (
        (None, {
            'fields': ('product', 'serial_number', 'barcode', 'status')
        }),
    )


class CartItemInline(admin.TabularInline):
    """
    Inline admin for CartItem model.
    """
    model = CartItem
    extra = 0
    fields = ('product', 'quantity', 'subtotal')
    readonly_fields = ('subtotal',)
    autocomplete_fields = ('product',)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin interface for the Cart model.
    """
    list_display = ('id', 'user', 'session_key', 'total_items', 'total_price', 'updated_at')
    search_fields = ('user__username', 'session_key')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('total_items', 'total_price', 'created_at', 'updated_at')
    inlines = [CartItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key')
        }),
        ('Cart Summary', {
            'fields': ('total_items', 'total_price')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Admin interface for the CartItem model.
    """
    list_display = ('id', 'cart', 'product', 'quantity', 'subtotal', 'updated_at')
    search_fields = ('product__name', 'cart__user__username')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('subtotal', 'created_at', 'updated_at')
    autocomplete_fields = ('cart', 'product')