# whatsappcrm_backend/opensolar_integration/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import (
    OpenSolarConfig,
    OpenSolarProject,
    OpenSolarWebhookLog,
    OpenSolarSyncLog
)


@admin.register(OpenSolarConfig)
class OpenSolarConfigAdmin(admin.ModelAdmin):
    list_display = [
        'organization_name',
        'org_id',
        'is_active',
        'auto_sync_enabled',
        'webhook_enabled',
        'created_at'
    ]
    list_filter = ['is_active', 'auto_sync_enabled', 'webhook_enabled']
    search_fields = ['organization_name', 'org_id']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Organization', {
            'fields': ('organization_name', 'org_id', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_base_url', 'api_timeout', 'api_retry_count')
        }),
        ('Webhook Configuration', {
            'fields': ('webhook_url', 'webhook_secret', 'webhook_enabled')
        }),
        ('Feature Flags', {
            'fields': ('auto_sync_enabled',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of active config
        if obj and obj.is_active:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(OpenSolarProject)
class OpenSolarProjectAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'customer_name',
        'opensolar_project_id',
        'project_status',
        'sync_status_badge',
        'last_synced_at',
        'created_at'
    ]
    list_filter = ['sync_status', 'project_status', 'created_at']
    search_fields = [
        'opensolar_project_id',
        'project_name',
        'installation_request__full_name',
        'installation_request__order_number'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_synced_at',
        'proposal_sent_at',
        'contract_signed_at'
    ]
    raw_id_fields = ['installation_request']
    
    fieldsets = (
        ('Installation Request', {
            'fields': ('installation_request',)
        }),
        ('OpenSolar Details', {
            'fields': (
                'opensolar_project_id',
                'opensolar_contact_id',
                'project_name',
                'project_status',
                'system_size_kw'
            )
        }),
        ('Proposal & Contract', {
            'fields': (
                'proposal_url',
                'proposal_sent_at',
                'contract_signed_at',
                'installation_scheduled_date'
            )
        }),
        ('Sync Status', {
            'fields': (
                'sync_status',
                'last_synced_at',
                'sync_error_message',
                'sync_retry_count'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_name(self, obj):
        return obj.installation_request.full_name
    customer_name.short_description = 'Customer'
    
    def sync_status_badge(self, obj):
        colors = {
            'synced': 'green',
            'pending': 'orange',
            'sync_failed': 'red',
            'updated': 'blue',
        }
        color = colors.get(obj.sync_status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_sync_status_display()
        )
    sync_status_badge.short_description = 'Sync Status'
    
    actions = ['sync_to_opensolar']
    
    def sync_to_opensolar(self, request, queryset):
        from .services import ProjectSyncService
        service = ProjectSyncService()
        
        success_count = 0
        for project in queryset:
            try:
                service.sync_installation_request(
                    project.installation_request,
                    force=True
                )
                success_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"Failed to sync project {project.id}: {str(e)}",
                    level='ERROR'
                )
        
        self.message_user(
            request,
            f"Successfully synced {success_count} project(s) to OpenSolar"
        )
    sync_to_opensolar.short_description = "Sync selected projects to OpenSolar"


@admin.register(OpenSolarWebhookLog)
class OpenSolarWebhookLogAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'event_type',
        'opensolar_project_id',
        'status_badge',
        'created_at'
    ]
    list_filter = ['status', 'event_type', 'created_at']
    search_fields = ['event_type', 'opensolar_project_id']
    readonly_fields = ['created_at', 'processed_at', 'payload', 'headers']
    raw_id_fields = ['project']
    
    fieldsets = (
        ('Webhook Details', {
            'fields': ('event_type', 'opensolar_project_id', 'project')
        }),
        ('Status', {
            'fields': ('status', 'processed_at', 'error_message')
        }),
        ('Data', {
            'fields': ('payload', 'headers'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'processed': 'green',
            'processing': 'blue',
            'received': 'gray',
            'failed': 'red',
            'ignored': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False  # Webhooks are created automatically


@admin.register(OpenSolarSyncLog)
class OpenSolarSyncLogAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'project',
        'sync_type',
        'status_badge',
        'duration_ms',
        'started_at'
    ]
    list_filter = ['status', 'sync_type', 'started_at']
    search_fields = ['project__opensolar_project_id']
    readonly_fields = [
        'started_at',
        'completed_at',
        'duration_ms',
        'request_data',
        'response_data'
    ]
    raw_id_fields = ['project']
    
    fieldsets = (
        ('Sync Details', {
            'fields': ('project', 'sync_type', 'status')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at', 'duration_ms')
        }),
        ('Data', {
            'fields': ('request_data', 'response_data', 'error_message'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'success': 'green',
            'started': 'blue',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def has_add_permission(self, request):
        return False  # Logs are created automatically
