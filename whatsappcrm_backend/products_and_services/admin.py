from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
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
    list_display = ('name', 'sku', 'barcode', 'product_type', 'category', 'price', 'is_active', 'stock_quantity', 'meta_sync_status', 'country_of_origin', 'brand', 'zoho_item_id')
    search_fields = ('name', 'sku', 'barcode', 'description', 'brand', 'zoho_item_id')
    list_filter = ('product_type', 'category', 'is_active', 'country_of_origin', 'brand')
    ordering = ('name',)
    inlines = [ProductImageInline]
    actions = ['reset_meta_sync_attempts', 'sync_to_meta_catalog', 'set_meta_visibility_published', 'set_meta_visibility_hidden', 'sync_selected_items']
    
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
        ('Integrations', {
            'fields': ('zoho_item_id',),
            'classes': ('collapse',),
            'description': 'Third-party integration identifiers'
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

    @admin.action(description='Sync selected products to Meta Catalog')
    def sync_to_meta_catalog(self, request, queryset):
        """
        Sync selected products to Meta Catalog.
        """
        from meta_integration.catalog_service import MetaCatalogService
        
        try:
            service = MetaCatalogService()
        except Exception as e:
            self.message_user(
                request,
                f'Failed to initialize Meta Catalog Service: {str(e)}',
                messages.ERROR
            )
            return
        
        success_count = 0
        error_count = 0
        skip_count = 0
        
        for product in queryset:
            if not product.sku:
                skip_count += 1
                continue
            
            if not product.is_active:
                skip_count += 1
                continue
            
            try:
                service.sync_product_update(product)
                success_count += 1
            except Exception as e:
                error_count += 1
        
        message_parts = []
        if success_count:
            message_parts.append(f'{success_count} synced successfully')
        if error_count:
            message_parts.append(f'{error_count} failed')
        if skip_count:
            message_parts.append(f'{skip_count} skipped (no SKU or inactive)')
        
        message = ', '.join(message_parts) if message_parts else 'No products to sync'
        level = messages.SUCCESS if error_count == 0 else messages.WARNING
        self.message_user(request, message, level)

    @admin.action(description='Set Meta visibility to PUBLISHED (active)')
    def set_meta_visibility_published(self, request, queryset):
        """
        Set visibility to 'published' for selected products in Meta Catalog.
        """
        self._set_meta_visibility(request, queryset, 'published')

    @admin.action(description='Set Meta visibility to HIDDEN (inactive)')
    def set_meta_visibility_hidden(self, request, queryset):
        """
        Set visibility to 'hidden' for selected products in Meta Catalog.
        """
        self._set_meta_visibility(request, queryset, 'hidden')

    def _set_meta_visibility(self, request, queryset, visibility):
        """
        Helper method to set visibility for multiple products.
        """
        from meta_integration.catalog_service import MetaCatalogService
        
        try:
            service = MetaCatalogService()
        except Exception as e:
            self.message_user(
                request,
                f'Failed to initialize Meta Catalog Service: {str(e)}',
                messages.ERROR
            )
            return
        
        # Filter products that have catalog IDs
        products_with_catalog = queryset.filter(whatsapp_catalog_id__isnull=False).exclude(whatsapp_catalog_id='')
        
        if not products_with_catalog.exists():
            self.message_user(
                request,
                'None of the selected products have been synced to Meta Catalog yet.',
                messages.WARNING
            )
            return
        
        # Build updates for batch operation
        updates = []
        for product in products_with_catalog:
            if product.sku:
                updates.append({
                    'product': product,
                    'data': {'visibility': visibility}
                })
        
        if not updates:
            self.message_user(
                request,
                'No eligible products found (products must have SKU and catalog ID).',
                messages.WARNING
            )
            return
        
        try:
            result = service.batch_update_products(updates)
            
            skipped = queryset.count() - len(updates)
            message = f'Visibility set to "{visibility}" for {len(updates)} product(s).'
            if skipped > 0:
                message += f' {skipped} product(s) skipped (no SKU or not synced).'
            
            self.message_user(request, message, messages.SUCCESS)
        except Exception as e:
            self.message_user(
                request,
                f'Failed to update visibility: {str(e)}',
                messages.ERROR
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
    @admin.action(description='Sync selected products from Zoho')
    def sync_selected_items(self, request, queryset):
        """
        Sync selected products from Zoho Inventory.
        Only products with zoho_item_id will be synced.
        """
        from integrations.utils import ZohoClient
        from decimal import Decimal
        
        # Filter products that have Zoho IDs
        products_with_zoho_id = queryset.filter(zoho_item_id__isnull=False).exclude(zoho_item_id='')
        
        if not products_with_zoho_id.exists():
            self.message_user(
                request,
                'None of the selected products have a Zoho Item ID.',
                messages.WARNING
            )
            return
        
        try:
            client = ZohoClient()
        except Exception as e:
            self.message_user(
                request,
                f'Failed to initialize Zoho client: {str(e)}',
                messages.ERROR
            )
            return
        
        success_count = 0
        error_count = 0
        
        for product in products_with_zoho_id:
            try:
                # Fetch specific item from Zoho
                # Note: This is a simplified approach. In production, you might want to
                # fetch items in batch or use a different API endpoint
                result = client.fetch_products(page=1, per_page=1)
                # For this action, we'll just trigger a full sync for simplicity
                # In a real implementation, you'd fetch specific items by ID
                
                self.message_user(
                    request,
                    f'Please use the "Sync Zoho" button in the top menu for full sync. '
                    f'Individual item sync is not implemented yet.',
                    messages.INFO
                )
                return
                
            except Exception as e:
                error_count += 1
        
        if success_count > 0:
            self.message_user(
                request,
                f'Successfully synced {success_count} product(s) from Zoho.',
                messages.SUCCESS
            )
        if error_count > 0:
            self.message_user(
                request,
                f'Failed to sync {error_count} product(s).',
                messages.ERROR
            )
