"""
Test that empty template parameters are handled correctly for Meta API.
This test verifies the fix for issue where Meta API rejects messages
with empty text parameter values.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from conversations.models import Contact
from meta_integration.models import MetaAppConfig
from .models import NotificationTemplate
from .services import queue_notifications_to_users

User = get_user_model()


class EmptyParameterHandlingTest(TestCase):
    """Test that empty parameters are properly handled when sending to Meta API"""
    
    def setUp(self):
        """Set up test data"""
        # Create a test contact
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='Test Customer'
        )
        
        # Create MetaAppConfig
        self.meta_config = MetaAppConfig.objects.create(
            name='Test Config',
            phone_number_id='123456789',
            access_token='test_token',
            waba_id='test_waba',
            is_active=True
        )
        
        # Create a notification template with body_parameters
        self.template = NotificationTemplate.objects.create(
            name='test_installation_notification',
            description='Test installation notification',
            message_body='Installation for {{ contact_name }} at {{ install_address }}{{ install_alt_contact_line }}{{ install_location_pin_line }}',
            body_parameters={
                '1': 'contact_name',
                '2': 'install_address',
                '3': 'install_alt_contact_line',
                '4': 'install_location_pin_line'
            }
        )
    
    @patch('notifications.services.send_whatsapp_message_task')
    def test_empty_conditional_fields_use_placeholder(self, mock_task):
        """Test that empty conditional fields use space placeholder instead of empty string"""
        # Context with some empty conditional fields
        context = {
            'contact_name': 'John Doe',
            'install_address': '123 Main St',
            'install_alt_name': 'N/A',  # This will make install_alt_contact_line empty
            'install_alt_phone': '',
            'install_alt_contact_line': '',  # Empty conditional field
            'install_location_pin': None,  # This will make install_location_pin_line empty
            'install_location_pin_line': ''  # Empty conditional field
        }
        
        # Queue notification
        queue_notifications_to_users(
            template_name='test_installation_notification',
            contact_ids=[self.contact.id],
            template_context=context
        )
        
        # Get the call arguments
        mock_task.delay.assert_called_once()
        call_args = mock_task.delay.call_args
        message_id = call_args[0][0]
        
        # Get the created message
        from conversations.models import Message
        message = Message.objects.get(id=message_id)
        
        # Verify the message was created with template type
        self.assertEqual(message.message_type, 'template')
        
        # Verify the payload has components
        self.assertIn('components', message.content_payload)
        components = message.content_payload['components']
        
        # Find the BODY component
        body_component = next((c for c in components if c['type'] == 'BODY'), None)
        self.assertIsNotNone(body_component)
        
        # Check parameters
        parameters = body_component['parameters']
        self.assertEqual(len(parameters), 4)
        
        # Verify non-empty parameters have correct values
        self.assertEqual(parameters[0]['text'], 'John Doe')
        self.assertEqual(parameters[1]['text'], '123 Main St')
        
        # Verify empty parameters use N/A placeholder (not empty string)
        self.assertEqual(parameters[2]['text'], 'N/A')  # install_alt_contact_line
        self.assertEqual(parameters[3]['text'], 'N/A')  # install_location_pin_line
        
        # Verify no parameter has empty string
        for param in parameters:
            self.assertNotEqual(param['text'], '', 
                              f"Parameter should not have empty string: {param}")
    
    @patch('notifications.services.send_whatsapp_message_task')
    def test_all_empty_parameters_use_placeholder(self, mock_task):
        """Test that all empty parameters use space placeholder"""
        # Context with all empty values
        context = {
            'contact_name': '',
            'install_address': '',
            'install_alt_contact_line': '',
            'install_location_pin_line': ''
        }
        
        # Queue notification
        queue_notifications_to_users(
            template_name='test_installation_notification',
            contact_ids=[self.contact.id],
            template_context=context
        )
        
        # Get the created message
        from conversations.models import Message
        message = Message.objects.filter(contact=self.contact).first()
        
        # Verify the message was created
        self.assertIsNotNone(message)
        
        # Get body component parameters
        body_component = next((c for c in message.content_payload['components'] 
                             if c['type'] == 'BODY'), None)
        parameters = body_component['parameters']
        
        # All parameters should have non-empty values
        # Note: contact_name would get default 'Contact', but install_address has no default
        # so it falls back to 'N/A'. Since we explicitly set them as empty in context,
        # contact_name gets default and install_address gets 'N/A'
        for i, param in enumerate(parameters):
            # Parameters can be either default values or N/A fallback
            self.assertNotEqual(param['text'], '', 
                           f"Parameter {i} should not be empty string: {param}")
            # At minimum should have some non-empty value
            self.assertTrue(param['text'].strip(), 
                          f"Parameter {i} should have non-empty value: {param}")
    
    @patch('notifications.services.send_whatsapp_message_task')
    def test_whitespace_only_parameters_use_placeholder(self, mock_task):
        """Test that whitespace-only parameters are converted to single space"""
        # Context with whitespace values
        context = {
            'contact_name': '   ',  # Multiple spaces
            'install_address': '\n\t',  # Tabs and newlines
            'install_alt_contact_line': '  \n  ',  # Mixed whitespace
            'install_location_pin_line': '\t\t'  # Tabs
        }
        
        # Queue notification
        queue_notifications_to_users(
            template_name='test_installation_notification',
            contact_ids=[self.contact.id],
            template_context=context
        )
        
        # Get the created message
        from conversations.models import Message
        message = Message.objects.filter(contact=self.contact).first()
        
        # Get body component parameters
        body_component = next((c for c in message.content_payload['components'] 
                             if c['type'] == 'BODY'), None)
        parameters = body_component['parameters']
        
        # All whitespace-only parameters should be converted to N/A or defaults
        for i, param in enumerate(parameters):
            # Should not be empty string or pure whitespace
            self.assertNotEqual(param['text'], '', 
                           f"Parameter {i} should not be empty string: {param}")
            self.assertTrue(param['text'].strip(), 
                          f"Parameter {i} should have non-empty/non-whitespace value: {param}")
    
    @patch('notifications.services.send_whatsapp_message_task')
    def test_mixed_empty_and_valid_parameters(self, mock_task):
        """Test that mix of empty and valid parameters works correctly"""
        # Context with mix of valid and empty values
        context = {
            'contact_name': 'Jane Smith',  # Valid
            'install_address': '',  # Empty
            'install_alt_contact_line': '- Alt: John (123-456)',  # Valid (newline removed)
            'install_location_pin_line': ''  # Empty
        }
        
        # Queue notification
        queue_notifications_to_users(
            template_name='test_installation_notification',
            contact_ids=[self.contact.id],
            template_context=context
        )
        
        # Get the created message
        from conversations.models import Message
        message = Message.objects.filter(contact=self.contact).first()
        
        # Get body component parameters
        body_component = next((c for c in message.content_payload['components'] 
                             if c['type'] == 'BODY'), None)
        parameters = body_component['parameters']
        
        # Check each parameter
        # Valid contact_name preserved
        self.assertEqual(parameters[0]['text'], 'Jane Smith')
        
        # Empty install_address should become N/A
        self.assertEqual(parameters[1]['text'], 'N/A')
        
        # Valid value preserved
        self.assertIn('Alt: John', parameters[2]['text'])
        
        # Empty location pin line should become N/A
        self.assertEqual(parameters[3]['text'], 'N/A')
    
    @patch('notifications.services.send_whatsapp_message_task')
    def test_order_notification_with_missing_customer_name(self, mock_task):
        """
        Test the specific bug: hanna_new_order_created template with empty customer_name.
        This replicates the actual error from the logs where customer_name was empty.
        """
        # Create order notification template
        order_template = NotificationTemplate.objects.create(
            name='test_order_notification',
            description='Test order notification',
            message_body='New order for {{ customer_name }}. Order: {{ order_name }}, #{{ order_number }}, Amount: ${{ order_amount }}',
            body_parameters={
                '1': 'customer_name',
                '2': 'order_name',
                '3': 'order_number',
                '4': 'order_amount'
            }
        )
        
        # Context similar to what's generated in customer_data/signals.py
        # when customer has no name (get_full_name() method returns empty string)
        # Note: 'get_full_name' here is the result of calling customer.get_full_name(),
        # not the method itself - this matches the actual signal structure
        context = {
            'order': {
                'id': '123',
                'name': 'Invoice 289634',
                'order_number': '289634',
                'amount': 0.0,
                'customer': {
                    'get_full_name': '',  # Result of customer.get_full_name() - empty!
                    'contact': {
                        'name': ''  # Also empty
                    }
                }
            }
        }
        
        # Queue notification
        queue_notifications_to_users(
            template_name='test_order_notification',
            contact_ids=[self.contact.id],
            template_context=context
        )
        
        # Get the created message
        from conversations.models import Message
        message = Message.objects.filter(contact=self.contact).first()
        
        # Verify message was created
        self.assertIsNotNone(message)
        
        # Get body component parameters
        body_component = next((c for c in message.content_payload['components'] 
                             if c['type'] == 'BODY'), None)
        self.assertIsNotNone(body_component)
        
        parameters = body_component['parameters']
        self.assertEqual(len(parameters), 4)
        
        # CRITICAL: customer_name should NOT be empty string (the bug we're fixing)
        # It should get the default 'Customer' value
        self.assertNotEqual(parameters[0]['text'], '', 
                          "customer_name parameter must not be empty string!")
        self.assertEqual(parameters[0]['text'], 'Customer', 
                       "Empty customer_name should default to 'Customer'")
        
        # Other parameters should have their expected values or defaults
        self.assertEqual(parameters[1]['text'], 'Invoice 289634')  # order_name
        self.assertEqual(parameters[2]['text'], '289634')  # order_number
        self.assertEqual(parameters[3]['text'], '0.0')  # order_amount

