# OpenSolar Integration - Technical Implementation

## Overview

This document provides technical details for implementing OpenSolar integration with the Hanna WhatsApp CRM system.

## Architecture

### Component Overview

```
whatsappcrm_backend/
├── opensolar_integration/          # New Django app
│   ├── __init__.py
│   ├── models.py                   # OpenSolar data models
│   ├── admin.py                    # Admin interface
│   ├── services.py                 # Business logic
│   ├── api_client.py              # OpenSolar API wrapper
│   ├── webhook_handlers.py        # Webhook processing
│   ├── serializers.py             # DRF serializers
│   ├── views.py                   # API endpoints
│   ├── urls.py                    # URL routing
│   ├── signals.py                 # Django signals
│   ├── tasks.py                   # Celery tasks
│   └── tests.py                   # Unit tests
```

## Database Models

### OpenSolarConfig

Stores OpenSolar API configuration and credentials.

```python
from django.db import models
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

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
```

### OpenSolarProject

Links Hanna installation requests to OpenSolar projects.

```python
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
```

### OpenSolarWebhookLog

Logs all webhook events from OpenSolar.

```python
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
```

### OpenSolarSyncLog

Tracks sync operations.

```python
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
```

## API Client Implementation

### api_client.py

```python
import requests
import logging
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from .models import OpenSolarConfig

logger = logging.getLogger(__name__)

class OpenSolarAPIClient:
    """
    Client for interacting with OpenSolar API.
    """
    
    def __init__(self, config: Optional[OpenSolarConfig] = None):
        """
        Initialize API client with configuration.
        """
        if config is None:
            config = OpenSolarConfig.objects.filter(is_active=True).first()
            if not config:
                raise ValueError("No active OpenSolar configuration found")
        
        self.config = config
        self.base_url = config.api_base_url.rstrip('/')
        self.org_id = config.org_id
        self.headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
        }
        self.timeout = config.api_timeout
        self.retry_count = config.api_retry_count
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to OpenSolar API with retry logic.
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"OpenSolar API {method} {url} (attempt {attempt + 1})")
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                logger.info(f"OpenSolar API {method} {url} - Success")
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"OpenSolar API {method} {url} - Error: {str(e)}")
                
                if attempt == self.retry_count - 1:
                    raise
                
                # Exponential backoff
                import time
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    # Project Methods
    
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project in OpenSolar.
        
        Args:
            project_data: Project details
            
        Returns:
            Created project data including project_id
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/"
        return self._make_request('POST', endpoint, data=project_data)
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project details from OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/{project_id}"
        return self._make_request('GET', endpoint)
    
    def update_project(
        self,
        project_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update project in OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/{project_id}"
        return self._make_request('PATCH', endpoint, data=update_data)
    
    def list_projects(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List projects from OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/"
        response = self._make_request('GET', endpoint, params=filters)
        return response.get('results', [])
    
    # Contact Methods
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new contact in OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/"
        return self._make_request('POST', endpoint, data=contact_data)
    
    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Get contact details from OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/{contact_id}"
        return self._make_request('GET', endpoint)
    
    def update_contact(
        self,
        contact_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact in OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/{contact_id}"
        return self._make_request('PATCH', endpoint, data=update_data)
    
    def find_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Find contact by phone number.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/"
        response = self._make_request('GET', endpoint, params={'phone': phone})
        results = response.get('results', [])
        return results[0] if results else None
    
    # Webhook Methods
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        List all webhooks for the organization.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/"
        response = self._make_request('GET', endpoint)
        return response.get('results', [])
    
    def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new webhook.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/"
        return self._make_request('POST', endpoint, data=webhook_data)
    
    def update_webhook(
        self,
        webhook_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update webhook configuration.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/{webhook_id}"
        return self._make_request('PATCH', endpoint, data=update_data)
    
    def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/{webhook_id}"
        self._make_request('DELETE', endpoint)
    
    # Helper Methods
    
    def test_connection(self) -> bool:
        """
        Test API connectivity.
        """
        try:
            self.list_projects()
            return True
        except Exception as e:
            logger.error(f"OpenSolar API connection test failed: {str(e)}")
            return False
```

## Service Layer

### services.py

```python
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from .models import OpenSolarProject, OpenSolarSyncLog
from .api_client import OpenSolarAPIClient
from customer_data.models import InstallationRequest

logger = logging.getLogger(__name__)

class ProjectSyncService:
    """
    Service for syncing installation requests to OpenSolar projects.
    """
    
    def __init__(self):
        self.api_client = OpenSolarAPIClient()
    
    def sync_installation_request(
        self,
        installation_request: InstallationRequest,
        force: bool = False
    ) -> OpenSolarProject:
        """
        Sync installation request to OpenSolar.
        
        Args:
            installation_request: InstallationRequest to sync
            force: Force resync even if already synced
            
        Returns:
            OpenSolarProject instance
        """
        # Get or create OpenSolarProject
        project, created = OpenSolarProject.objects.get_or_create(
            installation_request=installation_request
        )
        
        # Skip if already synced and not forcing
        if not created and project.sync_status == 'synced' and not force:
            logger.info(f"Project {project.id} already synced, skipping")
            return project
        
        # Start sync
        sync_log = OpenSolarSyncLog.objects.create(
            project=project,
            sync_type='create_project' if not project.opensolar_project_id else 'update_project',
            status='started'
        )
        
        start_time = timezone.now()
        
        try:
            # Prepare project data
            project_data = self._prepare_project_data(installation_request)
            
            # Create or update in OpenSolar
            if project.opensolar_project_id:
                response = self.api_client.update_project(
                    project.opensolar_project_id,
                    project_data
                )
            else:
                # First create/get contact
                contact_id = self._sync_contact(installation_request)
                project_data['contact_id'] = contact_id
                
                response = self.api_client.create_project(project_data)
                project.opensolar_project_id = response['id']
                project.opensolar_contact_id = contact_id
            
            # Update project with OpenSolar data
            project.project_name = response.get('name', '')
            project.project_status = response.get('status', '')
            project.system_size_kw = response.get('system_size_kw')
            project.sync_status = 'synced'
            project.last_synced_at = timezone.now()
            project.sync_error_message = ''
            project.sync_retry_count = 0
            project.save()
            
            # Update sync log
            end_time = timezone.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            sync_log.status = 'success'
            sync_log.completed_at = end_time
            sync_log.duration_ms = duration_ms
            sync_log.request_data = project_data
            sync_log.response_data = response
            sync_log.save()
            
            logger.info(f"Successfully synced project {project.id} to OpenSolar")
            
            return project
            
        except Exception as e:
            logger.error(f"Failed to sync project {project.id}: {str(e)}")
            
            # Update project
            project.sync_status = 'sync_failed'
            project.sync_error_message = str(e)
            project.sync_retry_count += 1
            project.save()
            
            # Update sync log
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            raise
    
    def _prepare_project_data(
        self,
        installation_request: InstallationRequest
    ) -> Dict[str, Any]:
        """
        Prepare project data for OpenSolar API.
        """
        customer = installation_request.customer
        
        return {
            'name': f"{customer.first_name} {customer.last_name} - Solar Installation",
            'type': 'residential',  # or 'commercial'
            'status': 'lead',  # Initial status
            'address': {
                'street': installation_request.installation_address or '',
                'city': installation_request.suburb or '',
                'state': '',
                'postal_code': '',
                'country': 'ZW',  # Zimbabwe
            },
            'notes': installation_request.notes or '',
            'custom_fields': {
                'hanna_installation_id': str(installation_request.id),
                'hanna_order_number': installation_request.order_number or '',
                'installation_type': installation_request.installation_type,
            }
        }
    
    def _sync_contact(self, installation_request: InstallationRequest) -> str:
        """
        Create or get contact in OpenSolar.
        
        Returns:
            OpenSolar contact ID
        """
        customer = installation_request.customer
        
        # Try to find existing contact by phone
        existing_contact = self.api_client.find_contact_by_phone(customer.phone_number)
        if existing_contact:
            logger.info(f"Found existing OpenSolar contact: {existing_contact['id']}")
            return existing_contact['id']
        
        # Create new contact
        contact_data = {
            'first_name': customer.first_name,
            'last_name': customer.last_name,
            'email': customer.email or '',
            'phone': customer.phone_number,
            'custom_fields': {
                'hanna_customer_id': str(customer.id),
                'source': 'whatsapp_crm',
            }
        }
        
        response = self.api_client.create_contact(contact_data)
        logger.info(f"Created new OpenSolar contact: {response['id']}")
        
        return response['id']
    
    def fetch_project_status(self, project: OpenSolarProject) -> Dict[str, Any]:
        """
        Fetch latest project status from OpenSolar.
        """
        if not project.opensolar_project_id:
            raise ValueError("Project not yet synced to OpenSolar")
        
        response = self.api_client.get_project(project.opensolar_project_id)
        
        # Update project with latest data
        project.project_status = response.get('status', '')
        project.system_size_kw = response.get('system_size_kw')
        project.proposal_url = response.get('proposal_url', '')
        project.last_synced_at = timezone.now()
        project.save()
        
        return response
```

## Webhook Handler

### webhook_handlers.py

```python
import logging
import hashlib
import hmac
from typing import Dict, Any
from django.utils import timezone
from django.conf import settings
from .models import OpenSolarWebhookLog, OpenSolarProject
from notifications.services import NotificationService

logger = logging.getLogger(__name__)

class WebhookProcessor:
    """
    Process incoming webhooks from OpenSolar.
    """
    
    def __init__(self):
        self.notification_service = NotificationService()
    
    def validate_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Validate webhook signature.
        """
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    def process_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> OpenSolarWebhookLog:
        """
        Process incoming webhook from OpenSolar.
        """
        # Extract project ID
        project_id = payload.get('project', {}).get('id')
        
        # Create webhook log
        webhook_log = OpenSolarWebhookLog.objects.create(
            event_type=event_type,
            opensolar_project_id=project_id,
            payload=payload,
            headers=headers,
            status='processing'
        )
        
        try:
            # Find associated project
            project = None
            if project_id:
                try:
                    project = OpenSolarProject.objects.get(
                        opensolar_project_id=project_id
                    )
                    webhook_log.project = project
                    webhook_log.save()
                except OpenSolarProject.DoesNotExist:
                    logger.warning(f"No project found for OpenSolar ID: {project_id}")
            
            # Process based on event type
            if event_type == 'project.status_changed':
                self._handle_status_change(project, payload)
            elif event_type == 'project.design_complete':
                self._handle_design_complete(project, payload)
            elif event_type == 'project.proposal_sent':
                self._handle_proposal_sent(project, payload)
            elif event_type == 'project.contract_signed':
                self._handle_contract_signed(project, payload)
            elif event_type == 'project.installation_scheduled':
                self._handle_installation_scheduled(project, payload)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
            
            # Mark as processed
            webhook_log.status = 'processed'
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            
            return webhook_log
            
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}", exc_info=True)
            webhook_log.status = 'failed'
            webhook_log.error_message = str(e)
            webhook_log.processed_at = timezone.now()
            webhook_log.save()
            raise
    
    def _handle_status_change(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle project status change."""
        if not project:
            return
        
        new_status = payload.get('project', {}).get('status')
        project.project_status = new_status
        project.save()
        
        # Update installation request status
        installation_request = project.installation_request
        status_map = {
            'lead': 'pending',
            'design': 'pending',
            'proposal': 'pending',
            'contract': 'scheduled',
            'installation': 'in_progress',
            'complete': 'completed',
        }
        
        if new_status in status_map:
            installation_request.status = status_map[new_status]
            installation_request.save()
        
        logger.info(f"Updated project status to: {new_status}")
    
    def _handle_design_complete(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle design completion."""
        if not project:
            return
        
        # Send notification to customer
        message = (
            f"Great news! Your solar system design is complete. "
            f"Our team will send you a detailed proposal shortly."
        )
        
        try:
            self.notification_service.send_whatsapp_message(
                to_phone=project.installation_request.customer.phone_number,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to send design complete notification: {str(e)}")
        
        logger.info(f"Design complete for project {project.id}")
    
    def _handle_proposal_sent(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle proposal sent."""
        if not project:
            return
        
        proposal_url = payload.get('project', {}).get('proposal_url', '')
        project.proposal_url = proposal_url
        project.proposal_sent_at = timezone.now()
        project.save()
        
        # Send notification with proposal link
        message = (
            f"Your solar installation proposal is ready! 🌞\n\n"
            f"View your personalized proposal here: {proposal_url}\n\n"
            f"Please review and let us know if you have any questions."
        )
        
        try:
            self.notification_service.send_whatsapp_message(
                to_phone=project.installation_request.customer.phone_number,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to send proposal notification: {str(e)}")
        
        logger.info(f"Proposal sent for project {project.id}")
    
    def _handle_contract_signed(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle contract signed."""
        if not project:
            return
        
        project.contract_signed_at = timezone.now()
        project.save()
        
        # Update installation request
        installation_request = project.installation_request
        installation_request.status = 'scheduled'
        installation_request.save()
        
        # Send confirmation
        message = (
            f"Thank you for signing the contract! 🎉\n\n"
            f"We're excited to install your solar system. "
            f"Our team will contact you soon to schedule the installation."
        )
        
        try:
            self.notification_service.send_whatsapp_message(
                to_phone=installation_request.customer.phone_number,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to send contract signed notification: {str(e)}")
        
        logger.info(f"Contract signed for project {project.id}")
    
    def _handle_installation_scheduled(
        self,
        project: Optional[OpenSolarProject],
        payload: Dict[str, Any]
    ):
        """Handle installation scheduled."""
        if not project:
            return
        
        install_date = payload.get('project', {}).get('installation_date')
        if install_date:
            from datetime import datetime
            project.installation_scheduled_date = datetime.fromisoformat(install_date).date()
            project.save()
        
        # Send confirmation
        message = (
            f"Your solar installation has been scheduled! 📅\n\n"
            f"Date: {install_date}\n\n"
            f"Our technicians will arrive on time and complete "
            f"the installation professionally. We'll send a reminder "
            f"closer to the date."
        )
        
        try:
            self.notification_service.send_whatsapp_message(
                to_phone=project.installation_request.customer.phone_number,
                message=message
            )
        except Exception as e:
            logger.error(f"Failed to send installation scheduled notification: {str(e)}")
        
        logger.info(f"Installation scheduled for project {project.id}")
```

## Next Steps

1. **Create Django App:**
   ```bash
   cd whatsappcrm_backend
   python manage.py startapp opensolar_integration
   ```

2. **Copy Model Code:**
   - Add models to `opensolar_integration/models.py`
   - Add API client to `opensolar_integration/api_client.py`
   - Add services to `opensolar_integration/services.py`
   - Add webhook handlers to `opensolar_integration/webhook_handlers.py`

3. **Register App:**
   - Add to `INSTALLED_APPS` in settings.py
   - Add URL patterns
   - Run migrations

4. **Configure Environment:**
   - Add OpenSolar credentials to `.env`
   - Update Django settings

5. **Test Integration:**
   - Test API connectivity
   - Test project creation
   - Test webhook processing

6. **Update Flows:**
   - Integrate with solar installation flow
   - Add notification templates
   - Test end-to-end

---

See `OPENSOLAR_INTEGRATION_GUIDE.md` for the complete integration guide.
