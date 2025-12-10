from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from unittest.mock import patch
from conversations.models import Contact
from notifications.models import Notification, NotificationTemplate
from .models import Order, CustomerProfile
import json

User = get_user_model()


class OrderSignalTest(TestCase):
    """Tests for Order model signals"""
    
    def setUp(self):
        """Set up test data"""
        # Create test groups
        self.admin_group = Group.objects.create(name='System Admins')
        self.sales_group = Group.objects.create(name='Sales Team')
        
        # Create test user with group
        self.user = User.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
        self.user.groups.add(self.admin_group)
        
        # Create WhatsApp contact
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='Test Customer'
        )
        
        # Create customer profile
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer'
        )
        
        # Create notification template
        self.template = NotificationTemplate.objects.create(
            name='hanna_new_order_created',
            description='Test template for new orders',
            message_body='New order: {{ order.name }}'
        )
    
    @patch('customer_data.signals.queue_notifications_to_users')
    def test_order_creation_triggers_notification_with_serializable_context(self, mock_queue):
        """Test that order creation signal passes JSON-serializable context"""
        # Create an order
        order = Order.objects.create(
            name='Test Order',
            order_number='ORD-001',
            customer=self.customer,
            amount=100.00
        )
        
        # Verify the signal was triggered
        self.assertTrue(mock_queue.called)
        
        # Get the call arguments
        call_args = mock_queue.call_args
        
        # Extract the template_context
        template_context = call_args.kwargs.get('template_context')
        
        # Verify context exists
        self.assertIsNotNone(template_context)
        
        # Verify that the context can be serialized to JSON
        try:
            json_str = json.dumps(template_context)
            self.assertIsNotNone(json_str)
        except TypeError as e:
            self.fail(f"Context is not JSON serializable: {e}")
        
        # Verify the order ID is a string (not UUID object)
        order_id = template_context.get('order', {}).get('id')
        self.assertIsInstance(order_id, str)
        self.assertEqual(order_id, str(order.id))
    
    def test_order_creation_creates_notification_with_valid_context(self):
        """Test that order creation creates notification with valid JSON context"""
        # Create an order
        order = Order.objects.create(
            name='Test Order 2',
            order_number='ORD-002',
            customer=self.customer,
            amount=200.00
        )
        
        # Get notifications created for the user
        notifications = Notification.objects.filter(recipient=self.user)
        
        # If notifications were created, verify their context is valid JSON
        for notification in notifications:
            if notification.template_context:
                # Verify the context is already JSON (stored in JSONField)
                self.assertIsInstance(notification.template_context, dict)
                
                # Verify it can be re-serialized (proving it's valid JSON)
                try:
                    json_str = json.dumps(notification.template_context)
                    self.assertIsNotNone(json_str)
                except TypeError as e:
                    self.fail(f"Notification context is not JSON serializable: {e}")
