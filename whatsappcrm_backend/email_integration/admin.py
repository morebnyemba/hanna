from django.contrib import admin
from django.utils.html import format_html
import json
from .models import EmailAttachment, ParsedInvoice, EmailAccount, AdminEmailRecipient, SMTPConfig


@admin.register(SMTPConfig)
class SMTPConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'username', 'use_tls', 'use_ssl', 'is_active', 'updated_at')
    list_filter = ('is_active', 'use_tls', 'use_ssl')
    search_fields = ('name', 'host', 'username')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Configuration Name', {
            'fields': ('name', 'is_active')
        }),
        ('SMTP Server Settings', {
            'fields': ('host', 'port', 'username', 'password')
        }),
        ('Encryption', {
            'fields': ('use_tls', 'use_ssl'),
            'description': 'Enable TLS for port 587 or SSL for port 465. Do not enable both.'
        }),
        ('Email Settings', {
            'fields': ('from_email', 'timeout')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Log when SMTP config is changed."""
        if change:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Admin {request.user.username} updated SMTP config: {obj.name}")
        super().save_model(request, obj, form, change)


@admin.register(AdminEmailRecipient)
class AdminEmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'email')
    list_editable = ('is_active',)

@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'imap_host', 'imap_user', 'is_active')
    list_filter = ('is_active', 'imap_host')
    search_fields = ('name', 'imap_user')

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'sender', 'processed', 'email_date', 'saved_at')
    list_filter = ('processed', 'email_date', 'sender')
    search_fields = ('filename', 'sender', 'subject')
    readonly_fields = ('saved_at', 'updated_at', 'pretty_extracted_data')
    fieldsets = (
        (None, {'fields': ('filename', 'sender', 'subject', 'email_date', 'processed')}),
        ('File Info', {'fields': ('file',)}),
        ('Extracted Data', {'fields': ('pretty_extracted_data',)}),
        ('Timestamps', {'fields': ('saved_at', 'updated_at')}),
    )

    def pretty_extracted_data(self, instance):
        """Displays the JSON data in a readable format."""
        if instance.extracted_data:
            # Convert the dict to a formatted string
            pretty_json = json.dumps(instance.extracted_data, indent=2)
            return format_html("<pre><code>{}</code></pre>", pretty_json)
        return "No data extracted."
    pretty_extracted_data.short_description = "Extracted Data (Formatted)"

@admin.register(ParsedInvoice)
class ParsedInvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'attachment_filename', 'invoice_date', 'total_amount')
    search_fields = ('invoice_number', 'attachment__filename')

    def attachment_filename(self, obj):
        return obj.attachment.filename
    attachment_filename.short_description = 'Attachment'