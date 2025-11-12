from django.test import TestCase
from django.utils import timezone
from unittest.mock import Mock, patch

from flows.models import WhatsAppFlow, WhatsAppFlowResponse
from flows.whatsapp_flow_response_processor import WhatsAppFlowResponseProcessor
from flows.definitions.starlink_installation_whatsapp_flow import STARLINK_INSTALLATION_WHATSAPP_FLOW
from conversations.models import Contact
from customer_data.models import CustomerProfile, InstallationRequest
from meta_integration.models import MetaAppConfig


class WhatsAppFlowModelTest(TestCase):
    """Tests for WhatsAppFlow model"""
    
    def setUp(self):
        # Create a test Meta app config
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
    
    def test_create_whatsapp_flow(self):
        """Test creating a WhatsAppFlow instance"""
        flow = WhatsAppFlow.objects.create(
            name="test_flow",
            friendly_name="Test Flow",
            description="A test flow",
            flow_json={"version": "3.0", "screens": []},
            meta_app_config=self.meta_config,
            sync_status='draft'
        )
        
        self.assertEqual(flow.name, "test_flow")
        self.assertEqual(flow.friendly_name, "Test Flow")
        self.assertEqual(flow.sync_status, 'draft')
        self.assertFalse(flow.is_active)
        self.assertIsNone(flow.flow_id)
    
    def test_whatsapp_flow_str(self):
        """Test string representation of WhatsAppFlow"""
        flow = WhatsAppFlow.objects.create(
            name="test_flow",
            flow_json={"version": "3.0"},
            meta_app_config=self.meta_config,
            sync_status='published'
        )
        
        self.assertEqual(str(flow), "Test Flow (Published)")
    
    def test_whatsapp_flow_friendly_name_auto_generated(self):
        """Test that friendly_name is auto-generated from name if not provided"""
        flow = WhatsAppFlow.objects.create(
            name="test_flow_name",
            flow_json={"version": "3.0"},
            meta_app_config=self.meta_config
        )
        
        self.assertEqual(flow.friendly_name, "Test Flow Name")


class WhatsAppFlowResponseModelTest(TestCase):
    """Tests for WhatsAppFlowResponse model"""
    
    def setUp(self):
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
        
        self.flow = WhatsAppFlow.objects.create(
            name="test_flow",
            flow_json={"version": "3.0"},
            meta_app_config=self.meta_config
        )
        
        self.contact = Contact.objects.create(
            whatsapp_id="1234567890",
            name="Test Contact",
            app_config=self.meta_config
        )
    
    def test_create_flow_response(self):
        """Test creating a WhatsAppFlowResponse instance"""
        response = WhatsAppFlowResponse.objects.create(
            whatsapp_flow=self.flow,
            contact=self.contact,
            flow_token="test_token_123",
            response_data={"full_name": "John Doe"},
            is_processed=False
        )
        
        self.assertEqual(response.whatsapp_flow, self.flow)
        self.assertEqual(response.contact, self.contact)
        self.assertEqual(response.flow_token, "test_token_123")
        self.assertFalse(response.is_processed)
        self.assertIsNone(response.processed_at)
    
    def test_flow_response_str(self):
        """Test string representation of WhatsAppFlowResponse"""
        response = WhatsAppFlowResponse.objects.create(
            whatsapp_flow=self.flow,
            contact=self.contact,
            flow_token="test_token",
            response_data={}
        )
        
        self.assertIn("Test Contact", str(response))
        self.assertIn("test_flow", str(response))


class WhatsAppFlowResponseProcessorTest(TestCase):
    """Tests for WhatsAppFlowResponseProcessor"""
    
    def setUp(self):
        self.meta_config = MetaAppConfig.objects.create(
            name="Test Config",
            verify_token="test_token",
            access_token="test_access_token",
            phone_number_id="123456789",
            waba_id="987654321",
            is_active=True
        )
        
        self.contact = Contact.objects.create(
            whatsapp_id="1234567890",
            name="Test Contact",
            app_config=self.meta_config
        )
    
    def test_process_starlink_installation_response(self):
        """Test processing Starlink installation flow response"""
        flow = WhatsAppFlow.objects.create(
            name="starlink_installation_whatsapp",
            flow_json=STARLINK_INSTALLATION_WHATSAPP_FLOW,
            meta_app_config=self.meta_config
        )
        
        response_data = {
            "data": {
                "full_name": "John Doe",
                "contact_phone": "+263771234567",
                "kit_type": "standard",
                "mount_location": "On the roof",
                "preferred_date": "2024-12-25",
                "availability": "morning",
                "address": "123 Main Street, Harare"
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            whatsapp_flow=flow,
            contact=self.contact,
            response_data=response_data
        )
        
        self.assertIsNotNone(flow_response)
        self.assertTrue(flow_response.is_processed)
        
        # Check that InstallationRequest was created
        installation_requests = InstallationRequest.objects.filter(
            customer__contact=self.contact
        )
        self.assertEqual(installation_requests.count(), 1)
        
        installation = installation_requests.first()
        self.assertEqual(installation.full_name, "John Doe")
        self.assertEqual(installation.installation_type, "starlink")
        self.assertEqual(installation.contact_phone, "+263771234567")
    
    def test_process_response_missing_required_fields(self):
        """Test processing response with missing required fields"""
        flow = WhatsAppFlow.objects.create(
            name="starlink_installation_whatsapp",
            flow_json=STARLINK_INSTALLATION_WHATSAPP_FLOW,
            meta_app_config=self.meta_config
        )
        
        response_data = {
            "data": {
                "full_name": "John Doe",
                # Missing contact_phone and address
            }
        }
        
        flow_response = WhatsAppFlowResponseProcessor.process_response(
            whatsapp_flow=flow,
            contact=self.contact,
            response_data=response_data
        )
        
        self.assertIsNotNone(flow_response)
        self.assertFalse(flow_response.is_processed)
        self.assertIn("Missing required fields", flow_response.processing_notes)


class WhatsAppFlowJSONDefinitionTest(TestCase):
    """Tests for WhatsApp Flow JSON definitions"""
    
    def test_starlink_flow_structure(self):
        """Test that Starlink flow JSON has required structure"""
        self.assertIn("version", STARLINK_INSTALLATION_WHATSAPP_FLOW)
        self.assertIn("screens", STARLINK_INSTALLATION_WHATSAPP_FLOW)
        self.assertEqual(STARLINK_INSTALLATION_WHATSAPP_FLOW["version"], "3.0")
        self.assertGreater(len(STARLINK_INSTALLATION_WHATSAPP_FLOW["screens"]), 0)
    
    def test_starlink_flow_has_welcome_screen(self):
        """Test that Starlink flow has WELCOME screen"""
        screens = STARLINK_INSTALLATION_WHATSAPP_FLOW["screens"]
        screen_ids = [screen["id"] for screen in screens]
        self.assertIn("WELCOME", screen_ids)
