from django.contrib import admin
from django.utils.html import format_html
from .models import ZohoCredential, OAuthState


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


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    """
    Admin interface for OAuthState model.
    """
    list_display = ['state_preview', 'user_id', 'used', 'is_valid_status', 'created_at']
    list_filter = ['used', 'created_at']
    readonly_fields = ['state', 'user_id', 'created_at', 'is_valid_status']
    search_fields = ['state', 'user_id']
    date_hierarchy = 'created_at'
    
    def state_preview(self, obj):
        """Display truncated state token."""
        return f"{obj.state[:20]}..."
    state_preview.short_description = "State Token"
    
    def is_valid_status(self, obj):
        """Display whether the state is valid."""
        if obj.is_valid():
            return format_html('<span style="color: green;">✅ Valid</span>')
        else:
            return format_html('<span style="color: red;">❌ Invalid/Expired</span>')
    is_valid_status.short_description = "Status"
    
    def has_add_permission(self, request):
        """Prevent manual creation of OAuth states."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of OAuth states."""
        return False
    
    actions = ['cleanup_expired_states']
    
    def cleanup_expired_states(self, request, queryset):
        """Admin action to cleanup expired state tokens."""
        count = OAuthState.cleanup_expired()
        self.message_user(request, f"Cleaned up {count} expired OAuth state token(s).")
    cleanup_expired_states.short_description = "Cleanup expired states"

