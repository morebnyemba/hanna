from django.db import models
from django.utils.timezone import now
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class SMTPConfigManager(models.Manager):
    def get_active_config(self):
        """
        Retrieves the single, globally active SMTPConfig.
        
        This is used as the default configuration for sending emails.
        If no active config exists, falls back to Django settings.
        """
        try:
            return self.get(is_active=True)
        except SMTPConfig.DoesNotExist:
            logger.warning("No active SMTP Configuration found in database. Falling back to Django settings.")
            return None
        except SMTPConfig.MultipleObjectsReturned:
            logger.error(
                "CRITICAL: Multiple SMTP Configurations are marked as active. "
                "Using most recently updated config. Please fix this in Django Admin."
            )
            # Use most recently updated config for predictable behavior
            return self.filter(is_active=True).order_by('-updated_at').first()


class SMTPConfig(models.Model):
    """
    Stores SMTP configuration for sending emails.
    Allows managing email settings via Django Admin instead of .env file.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="A descriptive name for this SMTP configuration (e.g., 'Primary Mail Server', 'Backup SMTP')"
    )
    host = models.CharField(
        max_length=255,
        help_text="SMTP server hostname (e.g., 'mail.example.com')"
    )
    port = models.PositiveIntegerField(
        default=587,
        help_text="SMTP server port. Common ports: 587 (TLS), 465 (SSL), 25 (plain)"
    )
    username = models.CharField(
        max_length=255,
        help_text="SMTP authentication username (usually an email address)"
    )
    password = models.CharField(
        max_length=255,
        help_text=(
            "SMTP authentication password. "
            "⚠️ WARNING: Stored as plain text in database. "
            "Use app-specific passwords and limit admin access. "
            "For production, consider implementing field-level encryption."
        )
    )
    use_tls = models.BooleanField(
        default=True,
        help_text="Use TLS (STARTTLS) encryption. Recommended for port 587."
    )
    use_ssl = models.BooleanField(
        default=False,
        help_text="Use SSL encryption. Recommended for port 465. Cannot be used with TLS."
    )
    from_email = models.EmailField(
        help_text="Default 'From' email address for outgoing emails"
    )
    timeout = models.PositiveIntegerField(
        default=10,
        help_text="Connection timeout in seconds"
    )
    is_active = models.BooleanField(
        default=False,
        help_text="Set to True to use this configuration. Only one configuration should be active."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SMTPConfigManager()

    class Meta:
        verbose_name = "SMTP Configuration"
        verbose_name_plural = "SMTP Configurations"
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} - {self.host}:{self.port} ({'Active' if self.is_active else 'Inactive'})"

    def clean(self):
        """Validate that TLS and SSL are not both enabled."""
        super().clean()
        if self.use_tls and self.use_ssl:
            raise ValidationError(
                "Cannot use both TLS and SSL. Please enable only one encryption method."
            )

    def save(self, *args, **kwargs):
        """Auto-deactivate other configs when this one is set to active."""
        from django.db import transaction
        
        self.full_clean()
        
        if self.is_active:
            # Use atomic transaction to prevent race conditions
            with transaction.atomic():
                # Deactivate all other configs atomically
                SMTPConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
                logger.info(f"SMTP Config '{self.name}' set as active. Other configs deactivated.")
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


class EmailAccount(models.Model):
    name = models.CharField(max_length=100, help_text="A friendly name for the email account, e.g., 'Sales Inbox'")
    imap_host = models.CharField(max_length=255)
    imap_user = models.CharField(max_length=255)
    imap_password = models.CharField(max_length=255)  # Consider using a more secure way to store this
    port = models.PositiveIntegerField(default=993, help_text="IMAP server port. Default is 993 for SSL.")
    ssl_protocol = models.CharField(
        max_length=20,
        choices=[
            ('auto', 'Auto (default)'),
            ('tls_v1_2', 'TLSv1.2'),
            ('tls_v1_3', 'TLSv1.3'),
        ],
        default='auto',
        help_text="Specify the SSL/TLS protocol version."
    )
    is_active = models.BooleanField(default=True, help_text="Enable or disable fetching from this account.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class EmailAttachment(models.Model):
    account = models.ForeignKey(EmailAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    sender = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    email_date = models.DateTimeField(blank=True, null=True) # Changed from CharField
    saved_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed = models.BooleanField(default=False, db_index=True)
    extracted_data = models.JSONField(blank=True, null=True, help_text="Structured data extracted by AI model.")

    def __str__(self):
        return f"{self.filename} (Processed: {self.processed})"

class ParsedInvoice(models.Model):
    """Stores structured data extracted from an email attachment."""
    attachment = models.OneToOneField(
        EmailAttachment,
        on_delete=models.CASCADE,
        related_name='parsed_invoice'
    )
    invoice_number = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    invoice_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    extracted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Invoice {self.invoice_number or 'N/A'} from {self.attachment.filename}"

class AdminEmailRecipient(models.Model):
    """
    Stores the email addresses of administrators who should receive critical error notifications.
    """
    name = models.CharField(max_length=100, help_text="Name of the administrator.")
    email = models.EmailField(unique=True, help_text="Email address to send notifications to.")
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck this to disable notifications for this recipient without deleting them."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"

    class Meta:
        verbose_name = "Admin Email Recipient"
        verbose_name_plural = "Admin Email Recipients"
        ordering = ['name']