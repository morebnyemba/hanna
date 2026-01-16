from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import (
    Warranty, WarrantyClaim, TechnicianComment, Manufacturer, Technician,
    WarrantyRule, SLAThreshold, SLAStatus
)


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
    list_display = ('serialized_item', 'manufacturer', 'customer', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'manufacturer', 'start_date', 'end_date', 'serialized_item__product__category')
    search_fields = ('serialized_item__serial_number', 'serialized_item__product__name', 'customer__first_name', 'customer__last_name', 'customer__contact__whatsapp_id')
    autocomplete_fields = ('serialized_item', 'customer', 'associated_order', 'manufacturer')
    inlines = [WarrantyClaimInline,]
    fieldsets = (
        ('Core Details', {
            'fields': ('serialized_item', 'manufacturer', 'customer', 'associated_order')
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
    search_fields = ('claim_id', 'warranty__serialized_item__serial_number', 'description_of_fault')
    readonly_fields = ('claim_id', 'created_at', 'updated_at')
    autocomplete_fields = ('warranty',)
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [TechnicianCommentInline,]

@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_email', 'user')
    search_fields = ('name', 'contact_email', 'user__username')
    autocomplete_fields = ('user',)

@admin.register(Technician)
class TechnicianAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'contact_phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialization')
    autocomplete_fields = ('user',)


@admin.register(WarrantyRule)
class WarrantyRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'product_category', 'warranty_duration_days', 'is_active', 'priority']
    list_filter = ['is_active', 'product_category']
    search_fields = ['name', 'product__name', 'product_category__name']
    ordering = ['-priority', '-created_at']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['product', 'product_category']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'is_active', 'priority')
        }),
        ('Rule Target', {
            'fields': ('product', 'product_category'),
            'description': 'Select either a specific product OR a product category, not both.'
        }),
        ('Warranty Details', {
            'fields': ('warranty_duration_days', 'terms_and_conditions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SLAThreshold)
class SLAThresholdAdmin(admin.ModelAdmin):
    list_display = ['name', 'request_type', 'response_time_hours', 'resolution_time_hours', 
                    'notification_threshold_percent', 'is_active']
    list_filter = ['is_active', 'request_type']
    search_fields = ['name']
    ordering = ['request_type', 'name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'request_type', 'is_active')
        }),
        ('Time Thresholds', {
            'fields': ('response_time_hours', 'resolution_time_hours')
        }),
        ('Escalation & Notifications', {
            'fields': ('escalation_rules', 'notification_threshold_percent'),
            'description': 'Notification threshold is the percentage of time elapsed before sending alerts (e.g., 80 for 80%).'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SLAStatus)
class SLAStatusAdmin(admin.ModelAdmin):
    list_display = ['id', 'sla_threshold', 'content_type', 'object_id', 
                    'response_status', 'resolution_status', 'request_created_at']
    list_filter = ['response_status', 'resolution_status', 'sla_threshold__request_type']
    search_fields = ['object_id']
    ordering = ['-request_created_at']
    readonly_fields = ['content_type', 'object_id', 'request_created_at', 
                       'response_time_deadline', 'resolution_time_deadline',
                       'response_completed_at', 'resolution_completed_at',
                       'created_at', 'updated_at']
    autocomplete_fields = ['sla_threshold']
    fieldsets = (
        ('Request Information', {
            'fields': ('content_type', 'object_id', 'sla_threshold', 'request_created_at')
        }),
        ('Response Tracking', {
            'fields': ('response_time_deadline', 'response_completed_at', 'response_status')
        }),
        ('Resolution Tracking', {
            'fields': ('resolution_time_deadline', 'resolution_completed_at', 'resolution_status')
        }),
        ('Notifications', {
            'fields': ('last_notification_sent',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """SLA statuses are created automatically, not manually"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of SLA tracking records"""
        return False