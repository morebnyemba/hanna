from django.contrib import admin
from .models import OfferingCategory, SoftwareProduct, ProfessionalService, Device, SoftwareModule

@admin.register(OfferingCategory)
class OfferingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'description')
    search_fields = ('name', 'description')
    list_filter = ('parent',)

class SoftwareModuleInline(admin.TabularInline):
    model = SoftwareModule
    extra = 1
    fields = ('name', 'price', 'sku', 'is_active')
    show_change_link = True

@admin.register(SoftwareProduct)
class SoftwareProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'license_type', 'is_saas', 'is_active')
    list_filter = ('is_active', 'category', 'license_type', 'is_saas')
    search_fields = ('name', 'sku', 'description')
    list_editable = ('price', 'is_active')
    autocomplete_fields = ['category']
    inlines = [SoftwareModuleInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active', 'sku', 'category')
        }),
        ('Product Details', {
            'fields': ('description', 'version', 'image')
        }),
        ('Pricing & Licensing', {
            'fields': (('price', 'currency'), 'license_type', 'is_saas')
        }),
    )

@admin.register(ProfessionalService)
class ProfessionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'currency', 'billing_cycle', 'is_active')
    list_filter = ('is_active', 'category', 'billing_cycle')
    search_fields = ('name', 'description')
    list_editable = ('price', 'is_active')
    autocomplete_fields = ['category']
    fieldsets = (
        (None, {
            'fields': ('name', 'is_active')
        }),
        ('Details', {
            'fields': ('description', 'category')
        }),
        ('Pricing & Billing', {
            'fields': (('price', 'currency'), 'billing_cycle')
        }),
    )

@admin.register(SoftwareModule)
class SoftwareModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'price', 'sku', 'is_active')
    list_filter = ('is_active', 'product')
    search_fields = ('name', 'sku', 'description', 'product__name')
    autocomplete_fields = ['product']
    filter_horizontal = ('compatible_devices',)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'model_number', 'sku', 'price', 'is_active', 'image_thumbnail')
    list_filter = ('is_active', 'manufacturer')
    search_fields = ('name', 'manufacturer', 'model_number', 'sku', 'description')
    list_editable = ('price', 'is_active')
    readonly_fields = ('image_thumbnail',) # To display the image in the admin
    fieldsets = (
        (None, {'fields': ('name', 'is_active', 'sku', 'manufacturer', 'model_number')}),
        ('Details', {'fields': ('description', ('price', 'currency'), 'image', 'image_thumbnail')}),
    )

    def image_thumbnail(self, obj):
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.image.url)
        return "No Image"
    image_thumbnail.short_description = "Image"
