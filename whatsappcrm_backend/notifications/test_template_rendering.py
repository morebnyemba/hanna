"""
Test template rendering for simplified templates.
Verifies that the fixed templates render correctly without Jinja2 errors.
"""
from django.test import TestCase
from notifications.utils import render_template_string


class TemplateRenderingTestCase(TestCase):
    """Test that simplified templates render correctly"""
    
    def test_human_handover_flow_template(self):
        """Test hanna_human_handover_flow template rendering"""
        template_body = """Human Intervention Required ⚠️

Contact *{{ related_contact_name }}* requires assistance.

*Reason:*
{{ last_bot_message }}

Please respond to them in the main inbox."""
        
        context = {
            'related_contact_name': 'John Doe',
            'last_bot_message': 'User requested help with payment'
        }
        
        result = render_template_string(template_body, context)
        
        self.assertIn('John Doe', result)
        self.assertIn('User requested help with payment', result)
        self.assertNotIn('{{', result)  # No unrendered variables
        self.assertNotIn('or ', result)  # No 'or' expressions left
    
    def test_message_send_failure_template(self):
        """Test hanna_message_send_failure template rendering"""
        template_body = """Message Send Failure ⚠️

Failed to send a message to *{{ related_contact_name }}*.

*Reason:* {{ error_details }}

Please check the system logs for more details."""
        
        context = {
            'related_contact_name': 'Jane Smith',
            'error_details': 'Network timeout'
        }
        
        result = render_template_string(template_body, context)
        
        self.assertIn('Jane Smith', result)
        self.assertIn('Network timeout', result)
        self.assertNotIn('{{', result)
        self.assertNotIn('Unknown error', result)  # No hardcoded defaults
    
    def test_invoice_processed_template(self):
        """Test hanna_invoice_processed_successfully template rendering"""
        template_body = """Invoice Processed Successfully ✅

An invoice from *{{ sender }}* (Filename: *{{ filename }}*) has been processed.

*Order Details:*
- Order #: *{{ order_number }}*
- Total Amount: *${{ order_amount }}*
- Customer: *{{ customer_name }}*

The new order has been created in the system."""
        
        context = {
            'sender': 'test@example.com',
            'filename': 'invoice_123.pdf',
            'order_number': 'PO-001',
            'order_amount': '150.00',
            'customer_name': 'Bob Johnson'
        }
        
        result = render_template_string(template_body, context)
        
        self.assertIn('test@example.com', result)
        self.assertIn('invoice_123.pdf', result)
        self.assertIn('PO-001', result)
        self.assertIn('150.00', result)
        self.assertIn('Bob Johnson', result)
        self.assertNotIn('{{', result)
        self.assertNotIn('|format', result)  # No filters left
        self.assertNotIn('if ', result)  # No conditionals left
    
    def test_missing_variable_renders_empty(self):
        """Test that missing variables render as empty string (SilentUndefined)"""
        template_body = "Hello {{ missing_var }}"
        context = {}
        
        result = render_template_string(template_body, context)
        
        # With SilentUndefined, missing vars become empty strings
        self.assertEqual(result.strip(), "Hello")
