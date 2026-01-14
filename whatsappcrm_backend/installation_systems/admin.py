from django.contrib import admin
from .models import InstallationSystemRecord, CommissioningChecklistTemplate, InstallationChecklistEntry, InstallationPhoto


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
    autocomplete_fields = ['customer', 'order', 'installation_request']
    filter_horizontal = ('technicians', 'installed_components', 'warranties', 'job_cards')
    list_per_page = 25
    list_select_related = ('customer', 'order', 'customer__contact')
    date_hierarchy = 'installation_date'
    
    fieldsets = (
        ('System Identification', {
            'fields': ('id', 'installation_request', 'customer', 'order')
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
        ('Assignment & Service', {
            'fields': ('technicians', 'installed_components', 'warranties', 'job_cards'),
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


@admin.register(CommissioningChecklistTemplate)
class CommissioningChecklistTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for the CommissioningChecklistTemplate model.
    """
    list_display = (
        'name',
        'checklist_type',
        'installation_type',
        'is_active',
        'item_count',
        'updated_at',
    )
    list_filter = (
        'checklist_type',
        'installation_type',
        'is_active',
        'created_at',
    )
    search_fields = (
        'name',
        'description',
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 25
    
    fieldsets = (
        ('Template Information', {
            'fields': ('id', 'name', 'checklist_type', 'installation_type', 'description', 'is_active')
        }),
        ('Checklist Items', {
            'fields': ('items',),
            'description': 'JSON array of checklist items. Each item should have: id, title, description, required, requires_photo, photo_count, notes_required'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        """Display count of items in the checklist"""
        return len(obj.items) if obj.items else 0
    item_count.short_description = "Items"


@admin.register(InstallationChecklistEntry)
class InstallationChecklistEntryAdmin(admin.ModelAdmin):
    """
    Admin interface for the InstallationChecklistEntry model.
    """
    list_display = (
        'short_id',
        'installation_record',
        'template',
        'completion_status',
        'completion_percentage',
        'technician',
        'updated_at',
    )
    list_filter = (
        'completion_status',
        'template__checklist_type',
        'created_at',
        'completed_at',
    )
    search_fields = (
        'installation_record__customer__first_name',
        'installation_record__customer__last_name',
        'template__name',
        'technician__user__username',
    )
    readonly_fields = ('id', 'completion_percentage', 'created_at', 'updated_at')
    autocomplete_fields = ['installation_record', 'technician']
    list_per_page = 25
    list_select_related = ('installation_record', 'template', 'technician', 'technician__user')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Checklist Information', {
            'fields': ('id', 'installation_record', 'template', 'technician')
        }),
        ('Completion Status', {
            'fields': (
                'completion_status',
                'completion_percentage',
                'started_at',
                'completed_at',
            )
        }),
        ('Completed Items Data', {
            'fields': ('completed_items',),
            'description': 'JSON object tracking completion of each checklist item'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def short_id(self, obj):
        """Display shortened UUID for readability"""
        return f"{str(obj.id)[:8]}"
    short_id.short_description = "ID"
    short_id.admin_order_field = 'id'


@admin.register(InstallationPhoto)
class InstallationPhotoAdmin(admin.ModelAdmin):
    """
    Admin interface for the InstallationPhoto model.
    """
    list_display = (
        'short_id',
        'installation_record_display',
        'photo_type',
        'caption',
        'is_required',
        'uploaded_by',
        'uploaded_at',
    )
    list_filter = (
        'photo_type',
        'is_required',
        'uploaded_at',
    )
    search_fields = (
        'caption',
        'description',
        'installation_record__customer__first_name',
        'installation_record__customer__last_name',
        'uploaded_by__user__username',
    )
    readonly_fields = ('id', 'uploaded_at', 'updated_at', 'media_preview')
    autocomplete_fields = ['installation_record', 'media_asset', 'uploaded_by']
    list_per_page = 25
    list_select_related = ('installation_record', 'media_asset', 'uploaded_by', 'uploaded_by__user')
    date_hierarchy = 'uploaded_at'
    
    fieldsets = (
        ('Photo Information', {
            'fields': ('id', 'installation_record', 'media_asset', 'media_preview')
        }),
        ('Photo Details', {
            'fields': (
                'photo_type',
                'caption',
                'description',
                'is_required',
                'checklist_item',
            )
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'uploaded_at', 'updated_at')
        }),
    )
    
    def short_id(self, obj):
        """Display shortened UUID for readability"""
        return f"{str(obj.id)[:8]}"
    short_id.short_description = "Photo ID"
    short_id.admin_order_field = 'id'
    
    def installation_record_display(self, obj):
        """Display shortened installation record ID"""
        return f"ISR-{str(obj.installation_record.id)[:8]}"
    installation_record_display.short_description = "Installation"
    installation_record_display.admin_order_field = 'installation_record'
    
    def media_preview(self, obj):
        """Display image preview if available"""
        if obj.media_asset and obj.media_asset.file:
            return f'<img src="{obj.media_asset.file.url}" style="max-width: 300px; max-height: 300px;" />'
        return "No preview available"
    media_preview.short_description = "Preview"
    media_preview.allow_tags = True
