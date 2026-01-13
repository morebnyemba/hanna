from django.contrib import admin
from .models import InstallationSystemRecord


@admin.register(InstallationSystemRecord)
class InstallationSystemRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for the InstallationSystemRecord model.
    """
    list_display = (
        'short_id',
        'customer',
        'installation_type',
        'system_classification',
        'system_capacity_display',
        'installation_status',
        'installation_date',
        'created_at',
    )
    list_filter = (
        'installation_type',
        'system_classification',
        'installation_status',
        'capacity_unit',
        'installation_date',
        'commissioning_date',
        'created_at',
    )
    search_fields = (
        'customer__first_name',
        'customer__last_name',
        'customer__contact__whatsapp_id',
        'installation_address',
        'remote_monitoring_id',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ['customer', 'order']
    filter_horizontal = ('technicians', 'installed_components')
    list_per_page = 25
    list_select_related = ('customer', 'order', 'customer__contact')
    date_hierarchy = 'installation_date'
    
    fieldsets = (
        ('System Identification', {
            'fields': ('id', 'customer', 'order')
        }),
        ('Installation Details', {
            'fields': (
                'installation_type',
                'system_classification',
                ('system_size', 'capacity_unit'),
            )
        }),
        ('Status & Dates', {
            'fields': (
                'installation_status',
                'installation_date',
                'commissioning_date',
            )
        }),
        ('Location & Monitoring', {
            'fields': (
                'installation_address',
                ('latitude', 'longitude'),
                'remote_monitoring_id',
            )
        }),
        ('Assignment', {
            'fields': ('technicians', 'installed_components'),
        }),
        ('System Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_id(self, obj):
        """Display shortened UUID for readability"""
        return f"ISR-{str(obj.id)[:8]}"
    short_id.short_description = "ISR ID"
    short_id.admin_order_field = 'id'
    
    def system_capacity_display(self, obj):
        """Display system size with unit"""
        if obj.system_size:
            return f"{obj.system_size} {obj.capacity_unit}"
        return "N/A"
    system_capacity_display.short_description = "System Capacity"
    system_capacity_display.admin_order_field = 'system_size'
