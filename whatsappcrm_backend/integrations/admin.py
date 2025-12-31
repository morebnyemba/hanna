from django.contrib import admin
from .models import ZohoCredential


@admin.register(ZohoCredential)
class ZohoCredentialAdmin(admin.ModelAdmin):
    """
    Admin interface for ZohoCredential model.
    """
    list_display = ('client_id_display', 'organization_id', 'token_status', 'expires_in', 'updated_at')
    fieldsets = (
        ('OAuth Credentials', {
            'fields': ('client_id', 'client_secret', 'scope')
        }),
        ('Organization Settings', {
            'fields': ('organization_id', 'api_domain')
        }),
        ('Token Information', {
            'fields': ('access_token', 'refresh_token', 'expires_in'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    def client_id_display(self, obj):
        """Display truncated client ID for security"""
        if obj.client_id:
            return f"{obj.client_id[:10]}..."
        return "Not set"
    client_id_display.short_description = 'Client ID'

    def token_status(self, obj):
        """Display whether token is valid or expired"""
        from django.utils.html import format_html
        if not obj.access_token:
            return format_html('<span style="color: red;">No Token</span>')
        elif obj.is_expired():
            return format_html('<span style="color: orange;">Expired</span>')
        else:
            return format_html('<span style="color: green;">Valid</span>')
    token_status.short_description = 'Token Status'

    def has_add_permission(self, request):
        """
        Only allow one instance (singleton).
        If an instance exists, don't show the 'Add' button.
        """
        if ZohoCredential.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        """
        Prevent deletion of the singleton instance.
        """
        return False
