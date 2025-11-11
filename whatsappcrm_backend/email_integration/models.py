from django.db import models
from django.utils.timezone import now

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