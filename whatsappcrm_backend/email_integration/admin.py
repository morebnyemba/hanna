from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
import json
import logging
import smtplib
import imaplib
import ssl
from email.mime.text import MIMEText
from .models import EmailAttachment, ParsedInvoice, EmailAccount, AdminEmailRecipient, SMTPConfig
from .tasks import process_attachment_with_gemini

logger = logging.getLogger(__name__)


@admin.action(description='Test SMTP connection for selected configuration')
def test_smtp_connection(modeladmin, request, queryset):
    """
    Admin action to test SMTP connection for selected configurations.
    Attempts to connect and authenticate without sending an email.
    """
    for config in queryset:
        try:
            # Create SMTP connection based on SSL/TLS settings
            if config.use_ssl:
                server = smtplib.SMTP_SSL(config.host, config.port, timeout=config.timeout)
            else:
                server = smtplib.SMTP(config.host, config.port, timeout=config.timeout)
                if config.use_tls:
                    server.starttls()
            
            # Authenticate
            server.login(config.username, config.password)
            server.quit()
            
            modeladmin.message_user(
                request,
                f"✓ SMTP connection successful for '{config.name}' ({config.host}:{config.port})",
                messages.SUCCESS
            )
            logger.info(f"Admin {request.user.username} successfully tested SMTP config: {config.name}")
            
        except smtplib.SMTPAuthenticationError as e:
            modeladmin.message_user(
                request,
                f"✗ Authentication failed for '{config.name}': {str(e)}",
                messages.ERROR
            )
            logger.error(f"SMTP authentication failed for {config.name}: {e}")
            
        except smtplib.SMTPException as e:
            modeladmin.message_user(
                request,
                f"✗ SMTP error for '{config.name}': {str(e)}",
                messages.ERROR
            )
            logger.error(f"SMTP error for {config.name}: {e}")
            
        except Exception as e:
            modeladmin.message_user(
                request,
                f"✗ Connection failed for '{config.name}': {str(e)}",
                messages.ERROR
            )
            logger.error(f"Connection failed for {config.name}: {e}")


@admin.register(SMTPConfig)
class SMTPConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'username', 'use_tls', 'use_ssl', 'is_active', 'updated_at')
    list_filter = ('is_active', 'use_tls', 'use_ssl')
    search_fields = ('name', 'host', 'username')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    actions = [test_smtp_connection]
    
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
            logger.info(f"Admin {request.user.username} updated SMTP config: {obj.name}")
        super().save_model(request, obj, form, change)


@admin.register(AdminEmailRecipient)
class AdminEmailRecipientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'email')
    list_editable = ('is_active',)

@admin.action(description='Retrigger Gemini processing for selected attachments')
def retrigger_gemini_processing(modeladmin, request, queryset):
    """
    Admin action to retrigger Gemini processing for selected email attachments.
    This is useful when processing failed or when you want to reprocess attachments.
    """
    success_count = 0
    already_queued = 0
    
    for attachment in queryset:
        # Reset the processed flag to allow reprocessing
        attachment.processed = False
        attachment.save(update_fields=['processed'])
        
        # Queue the attachment for Gemini processing
        try:
            process_attachment_with_gemini.delay(attachment.id)
            success_count += 1
            logger.info(f"Admin {request.user.username} retriggered Gemini processing for attachment {attachment.id}")
        except Exception as e:
            logger.error(f"Failed to queue attachment {attachment.id} for processing: {e}")
            already_queued += 1
    
    if success_count > 0:
        modeladmin.message_user(
            request,
            f"Successfully queued {success_count} attachment(s) for Gemini processing.",
            messages.SUCCESS
        )
    
    if already_queued > 0:
        modeladmin.message_user(
            request,
            f"Failed to queue {already_queued} attachment(s). Check logs for details.",
            messages.WARNING
        )


@admin.action(description='Mark selected attachments as unprocessed')
def mark_as_unprocessed(modeladmin, request, queryset):
    """
    Admin action to mark selected attachments as unprocessed.
    This allows them to be picked up by automated processing tasks.
    """
    updated_count = queryset.update(processed=False)
    modeladmin.message_user(
        request,
        f"{updated_count} attachment(s) marked as unprocessed.",
        messages.SUCCESS
    )
    logger.info(f"Admin {request.user.username} marked {updated_count} attachments as unprocessed")


@admin.action(description='Mark selected attachments as processed')
def mark_as_processed(modeladmin, request, queryset):
    """
    Admin action to mark selected attachments as processed.
    This prevents them from being reprocessed automatically.
    """
    updated_count = queryset.update(processed=True)
    modeladmin.message_user(
        request,
        f"{updated_count} attachment(s) marked as processed.",
        messages.SUCCESS
    )
    logger.info(f"Admin {request.user.username} marked {updated_count} attachments as processed")


@admin.action(description='Test IMAP connection for selected accounts')
def test_imap_connection(modeladmin, request, queryset):
    """
    Admin action to test IMAP connection for selected email accounts.
    Attempts to connect and authenticate to verify credentials.
    """
    for account in queryset:
        try:
            # Determine SSL context based on protocol setting
            context = ssl.create_default_context()
            
            if account.ssl_protocol == 'tls_v1_2':
                # Set minimum TLS version to 1.2
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.maximum_version = ssl.TLSVersion.TLSv1_2
            elif account.ssl_protocol == 'tls_v1_3':
                # Set minimum TLS version to 1.3
                context.minimum_version = ssl.TLSVersion.TLSv1_3
            # For 'auto', use default secure context (no version constraints)
            
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(account.imap_host, account.port, ssl_context=context)
            mail.login(account.imap_user, account.imap_password)
            
            # Get mailbox status
            status, messages = mail.select('INBOX')
            if status == 'OK':
                message_count = messages[0].decode('utf-8')
                mail.logout()
                
                modeladmin.message_user(
                    request,
                    f"✓ IMAP connection successful for '{account.name}'. Inbox has {message_count} message(s).",
                    messages.SUCCESS
                )
                logger.info(f"Admin {request.user.username} successfully tested IMAP account: {account.name}")
            else:
                mail.logout()
                modeladmin.message_user(
                    request,
                    f"⚠ Connected to '{account.name}' but couldn't access INBOX.",
                    messages.WARNING
                )
                
        except imaplib.IMAP4.error as e:
            modeladmin.message_user(
                request,
                f"✗ IMAP authentication failed for '{account.name}': {str(e)}",
                messages.ERROR
            )
            logger.error(f"IMAP authentication failed for {account.name}: {e}")
            
        except Exception as e:
            modeladmin.message_user(
                request,
                f"✗ Connection failed for '{account.name}': {str(e)}",
                messages.ERROR
            )
            logger.error(f"IMAP connection failed for {account.name}: {e}")


@admin.register(EmailAccount)
class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'imap_host', 'imap_user', 'is_active')
    list_filter = ('is_active', 'imap_host')
    search_fields = ('name', 'imap_user')
    actions = [test_imap_connection]

@admin.register(EmailAttachment)
class EmailAttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'sender', 'processed', 'email_date', 'saved_at')
    list_filter = ('processed', 'email_date', 'sender')
    search_fields = ('filename', 'sender', 'subject')
    readonly_fields = ('saved_at', 'updated_at', 'pretty_extracted_data')
    actions = [retrigger_gemini_processing, mark_as_unprocessed, mark_as_processed]
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