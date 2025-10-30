from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Warranty, WarrantyClaim, TechnicianComment, Manufacturer


class TechnicianCommentInline(GenericTabularInline):
    model = TechnicianComment
    extra = 1
    fields = ('technician', 'comment', 'created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('technician',)
    ordering = ('-created_at',)


class WarrantyClaimInline(admin.TabularInline):
    model = WarrantyClaim
    extra = 0
    fields = ('claim_id', 'status', 'description_of_fault', 'created_at')
    readonly_fields = ('claim_id', 'description_of_fault', 'created_at')
    show_change_link = True


@admin.register(Warranty)
class WarrantyAdmin(admin.ModelAdmin):
    list_display = ('product_serial_number', 'product', 'manufacturer', 'customer', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'manufacturer', 'start_date', 'end_date', 'product__category')
    search_fields = ('product_serial_number', 'product__name', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    autocomplete_fields = ('product', 'customer', 'associated_order', 'manufacturer')
    inlines = [WarrantyClaimInline,]
    fieldsets = (
        ('Core Details', {
            'fields': ('product', 'manufacturer', 'customer', 'product_serial_number', 'associated_order')
        }),
        ('Warranty Period & Status', {
            'fields': ('status', 'start_date', 'end_date')
        }),
        ('Manufacturer', {'fields': ('manufacturer_email',)}),
    )


@admin.register(WarrantyClaim)
class WarrantyClaimAdmin(admin.ModelAdmin):
    list_display = ('claim_id', 'warranty', 'status', 'created_at', 'job_card')
    list_filter = ('status', 'created_at')
    search_fields = ('claim_id', 'warranty__product_serial_number', 'description_of_fault')
    readonly_fields = ('claim_id', 'created_at', 'updated_at')
    autocomplete_fields = ('warranty', 'job_card')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [TechnicianCommentInline,]

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'user')
    search_fields = ('name', 'contact_email', 'user__username')
    autocomplete_fields = ('user',)