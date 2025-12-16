# whatsappcrm_backend/opensolar_integration/tests.py

from django.test import TestCase
from django.utils import timezone
from customer_data.models import CustomerProfile, InstallationRequest
from .models import OpenSolarConfig, OpenSolarProject, OpenSolarWebhookLog
from .services import ProjectSyncService
from unittest.mock import patch, MagicMock


class OpenSolarConfigTestCase(TestCase):
    """Tests for OpenSolarConfig model."""
    
    def test_only_one_active_config(self):
        """Test that only one config can be active at a time."""
        config1 = OpenSolarConfig.objects.create(
            organization_name="Test Org 1",
            org_id="org1",
            api_key="key1",
            is_active=True
        )
        
        config2 = OpenSolarConfig.objects.create(
            organization_name="Test Org 2",
            org_id="org2",
            api_key="key2",
            is_active=True
        )
        
        # Refresh config1 from database
        config1.refresh_from_db()
        
        # config1 should now be inactive
        self.assertFalse(config1.is_active)
        self.assertTrue(config2.is_active)


class OpenSolarProjectTestCase(TestCase):
    """Tests for OpenSolarProject model."""
    
    def setUp(self):
        self.customer = CustomerProfile.objects.create(
            phone_number="+263771234567",
            first_name="Test",
            last_name="Customer"
        )
        
        self.installation_request = InstallationRequest.objects.create(
            customer=self.customer,
            full_name="Test Customer",
            installation_type="solar",
            status="pending"
        )
    
    def test_create_opensolar_project(self):
        """Test creating an OpenSolar project link."""
        project = OpenSolarProject.objects.create(
            installation_request=self.installation_request,
            opensolar_project_id="os-123",
            project_status="lead"
        )
        
        self.assertEqual(project.sync_status, 'pending')
        self.assertEqual(project.opensolar_project_id, 'os-123')
        self.assertIsNone(project.last_synced_at)
    
    def test_one_to_one_relationship(self):
        """Test that installation request can only have one OpenSolar project."""
        OpenSolarProject.objects.create(
            installation_request=self.installation_request
        )
        
        # Creating another should raise error
        with self.assertRaises(Exception):
            OpenSolarProject.objects.create(
                installation_request=self.installation_request
            )


class ProjectSyncServiceTestCase(TestCase):
    """Tests for ProjectSyncService."""
    
    def setUp(self):
        self.config = OpenSolarConfig.objects.create(
            organization_name="Test Org",
            org_id="test-org",
            api_key="test-key",
            is_active=True
        )
        
        self.customer = CustomerProfile.objects.create(
            phone_number="+263771234567",
            first_name="Test",
            last_name="Customer",
            email="test@example.com"
        )
        
        self.installation_request = InstallationRequest.objects.create(
            customer=self.customer,
            full_name="Test Customer",
            installation_type="solar",
            status="pending",
            installation_address="123 Test St",
            suburb="Test City"
        )
    
    @patch('opensolar_integration.api_client.OpenSolarAPIClient._make_request')
    def test_prepare_project_data(self, mock_request):
        """Test project data preparation."""
        service = ProjectSyncService()
        data = service._prepare_project_data(self.installation_request)
        
        self.assertEqual(data['name'], 'Test Customer - Solar Installation')
        self.assertEqual(data['type'], 'residential')
        self.assertEqual(data['address']['city'], 'Test City')
        self.assertEqual(
            data['custom_fields']['installation_type'],
            'solar'
        )
    
    @patch('opensolar_integration.api_client.OpenSolarAPIClient.find_contact_by_phone')
    @patch('opensolar_integration.api_client.OpenSolarAPIClient.create_contact')
    def test_sync_contact_creates_new(self, mock_create, mock_find):
        """Test creating new contact in OpenSolar."""
        mock_find.return_value = None
        mock_create.return_value = {'id': 'contact-123'}
        
        service = ProjectSyncService()
        contact_id = service._sync_contact(self.installation_request)
        
        self.assertEqual(contact_id, 'contact-123')
        mock_create.assert_called_once()


class WebhookProcessorTestCase(TestCase):
    """Tests for webhook processing."""
    
    def setUp(self):
        self.customer = CustomerProfile.objects.create(
            phone_number="+263771234567",
            first_name="Test",
            last_name="Customer"
        )
        
        self.installation_request = InstallationRequest.objects.create(
            customer=self.customer,
            full_name="Test Customer",
            installation_type="solar",
            status="pending"
        )
        
        self.project = OpenSolarProject.objects.create(
            installation_request=self.installation_request,
            opensolar_project_id="os-123",
            sync_status="synced"
        )
    
    def test_process_webhook_creates_log(self):
        """Test that webhook processing creates a log."""
        from .webhook_handlers import WebhookProcessor
        
        processor = WebhookProcessor()
        payload = {
            'event_type': 'project.status_changed',
            'project': {
                'id': 'os-123',
                'status': 'design'
            }
        }
        
        webhook_log = processor.process_webhook(
            event_type='project.status_changed',
            payload=payload,
            headers={}
        )
        
        self.assertEqual(webhook_log.status, 'processed')
        self.assertEqual(webhook_log.event_type, 'project.status_changed')
        self.assertIsNotNone(webhook_log.processed_at)
    
    def test_status_change_updates_project(self):
        """Test that status change webhook updates project."""
        from .webhook_handlers import WebhookProcessor
        
        processor = WebhookProcessor()
        payload = {
            'project': {
                'id': 'os-123',
                'status': 'contract'
            }
        }
        
        processor._handle_status_change(self.project, payload)
        
        self.project.refresh_from_db()
        self.assertEqual(self.project.project_status, 'contract')
        
        self.installation_request.refresh_from_db()
        self.assertEqual(self.installation_request.status, 'scheduled')
