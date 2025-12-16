# whatsappcrm_backend/opensolar_integration/models.py

from django.db import models
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)


class OpenSolarConfig(models.Model):
    """
    Configuration for OpenSolar API integration.
    Should have only one active instance.
    """
    organization_name = models.CharField(
        max_length=255,
        help_text="Your organization name in OpenSolar"
    )
    org_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="OpenSolar Organization ID"
    )
    api_key = models.CharField(
        max_length=255,
        help_text="OpenSolar API Bearer Token"
    )
    api_base_url = models.URLField(
        default="https://api.opensolar.com",
        validators=[URLValidator()],
        help_text="OpenSolar API base URL"
    )
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Secret for validating incoming webhooks"
    )
    webhook_url = models.URLField(
        blank=True,
        help_text="URL where OpenSolar sends webhooks"
    )
    
    # Feature flags
    auto_sync_enabled = models.BooleanField(
        default=True,
        help_text="Automatically sync installation requests to OpenSolar"
    )
    webhook_enabled = models.BooleanField(
        default=True,
        help_text="Process incoming webhooks from OpenSolar"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Is this configuration active?"
    )
    
    # API settings
    api_timeout = models.IntegerField(
        default=30,
        help_text="API request timeout in seconds"
    )
    api_retry_count = models.IntegerField(
        default=3,
        help_text="Number of retries for failed API calls"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "OpenSolar Configuration"
        verbose_name_plural = "OpenSolar Configurations"
    
    def __str__(self):
        return f"{self.organization_name} - {'Active' if self.is_active else 'Inactive'}"
    
    def save(self, *args, **kwargs):
        # Ensure only one active config
        if self.is_active:
            OpenSolarConfig.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class OpenSolarProject(models.Model):
    """
    Links InstallationRequest to OpenSolar project.
    Tracks sync status and OpenSolar project details.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Sync'),
        ('synced', 'Synced'),
        ('sync_failed', 'Sync Failed'),
        ('updated', 'Updated in OpenSolar'),
    ]
    
    # Link to Hanna models
    installation_request = models.OneToOneField(
        'customer_data.InstallationRequest',
        on_delete=models.CASCADE,
        related_name='opensolar_project',
        help_text="Associated installation request"
    )
    
    # OpenSolar project details
    opensolar_project_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="OpenSolar project ID"
    )
    opensolar_contact_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="OpenSolar contact ID for the customer"
    )
    
    # Project details from OpenSolar
    project_name = models.CharField(max_length=255, blank=True)
    project_status = models.CharField(max_length=50, blank=True)
    system_size_kw = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="System size in kW"
    )
    proposal_url = models.URLField(
        blank=True,
        help_text="URL to OpenSolar proposal"
    )
    proposal_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When proposal was sent to customer"
    )
    contract_signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When customer signed the contract"
    )
    installation_scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Scheduled installation date"
    )
    
    # Sync status
    sync_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    last_synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last successful sync timestamp"
    )
    sync_error_message = models.TextField(
        blank=True,
        help_text="Error message from last failed sync"
    )
    sync_retry_count = models.IntegerField(
        default=0,
        help_text="Number of sync retry attempts"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "OpenSolar Project"
        verbose_name_plural = "OpenSolar Projects"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OpenSolar Project {self.opensolar_project_id or 'Pending'} - {self.installation_request.full_name}"


class OpenSolarWebhookLog(models.Model):
    """
    Logs all webhook events received from OpenSolar.
    """
    
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('ignored', 'Ignored'),
    ]
    
    # Webhook details
    event_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Type of webhook event"
    )
    opensolar_project_id = models.CharField(
        max_length=100,
        db_index=True,
        help_text="OpenSolar project ID from webhook"
    )
    
    # Payload
    payload = models.JSONField(
        help_text="Full webhook payload"
    )
    headers = models.JSONField(
        default=dict,
        help_text="Request headers"
    )
    
    # Processing status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='received',
        db_index=True
    )
    processed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if processing failed"
    )
    
    # Link to our project
    project = models.ForeignKey(
        OpenSolarProject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_logs'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = "OpenSolar Webhook Log"
        verbose_name_plural = "OpenSolar Webhook Logs"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.status} - {self.created_at}"


class OpenSolarSyncLog(models.Model):
    """
    Tracks synchronization operations between Hanna and OpenSolar.
    """
    
    SYNC_TYPE_CHOICES = [
        ('create_project', 'Create Project'),
        ('update_project', 'Update Project'),
        ('create_contact', 'Create Contact'),
        ('update_contact', 'Update Contact'),
        ('fetch_status', 'Fetch Status'),
    ]
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]
    
    project = models.ForeignKey(
        OpenSolarProject,
        on_delete=models.CASCADE,
        related_name='sync_logs'
    )
    sync_type = models.CharField(
        max_length=50,
        choices=SYNC_TYPE_CHOICES,
        db_index=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='started',
        db_index=True
    )
    
    # Request/Response details
    request_data = models.JSONField(
        default=dict,
        help_text="Data sent to OpenSolar"
    )
    response_data = models.JSONField(
        default=dict,
        help_text="Response from OpenSolar"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if sync failed"
    )
    
    # Timing
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )
    duration_ms = models.IntegerField(
        null=True,
        blank=True,
        help_text="Sync duration in milliseconds"
    )
    
    class Meta:
        verbose_name = "OpenSolar Sync Log"
        verbose_name_plural = "OpenSolar Sync Logs"
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['-started_at', 'status']),
        ]
    
    def __str__(self):
        return f"{self.sync_type} - {self.status} - {self.started_at}"
