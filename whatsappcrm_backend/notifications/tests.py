# whatsappcrm_backend/notifications/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from unittest.mock import patch, MagicMock
from conversations.models import Contact
from meta_integration.models import MetaAppConfig
from .models import Notification, NotificationTemplate
from .services import queue_notifications_to_users
from .tasks import dispatch_notification_task

User = get_user_model()


class NotificationSystemSetupTest(TestCase):
    """Tests to verify notification system is properly configured"""
    
    def setUp(self):
        """Set up test data"""
        # Create test groups
        self.tech_admin_group = Group.objects.create(name='Technical Admin')
        self.sales_group = Group.objects.create(name='Sales Team')
        
        # Create test user with group
        self.user = User.objects.create_user(
            username='testadmin',
            email='test@example.com',
            password='testpass123'
        )
        self.user.groups.add(self.tech_admin_group)
        
        # Create WhatsApp contact and link to user
        self.contact = Contact.objects.create(
            whatsapp_id='+263771234567',
            name='Test Admin'
        )
        self.contact.user = self.user
        self.contact.save()
        
        # Create a notification template
        self.template = NotificationTemplate.objects.create(
            name='test_notification',
            description='Test notification template',
            message_body='Hello {{ recipient.first_name }}, this is a test message.',
        )
    
    def test_groups_can_be_created(self):
        """Test that required groups can be created"""
        required_groups = [
            'Technical Admin',
            'System Admins',
            'Sales Team',
            'Pastoral Team',
            'Pfungwa Staff',
            'Finance Team'
        ]
        
        for group_name in required_groups:
            group, created = Group.objects.get_or_create(name=group_name)
            self.assertIsNotNone(group)
            self.assertEqual(group.name, group_name)
    
    def test_user_can_be_linked_to_contact(self):
        """Test that user can be linked to WhatsApp contact"""
        self.assertEqual(self.user.whatsapp_contact, self.contact)
        self.assertEqual(self.contact.user, self.user)
    
    def test_notification_template_exists(self):
        """Test that notification template can be created"""
        template = NotificationTemplate.objects.get(name='test_notification')
        self.assertIsNotNone(template)
        self.assertEqual(template.name, 'test_notification')
    
    def test_queue_notification_by_group(self):
        """Test queuing notification by group name"""
        queue_notifications_to_users(
            template_name='test_notification',
            group_names=['Technical Admin'],
            template_context={'recipient': self.user}
        )
        
        # Check notification was created
        notification = Notification.objects.filter(recipient=self.user).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.status, 'pending')
        self.assertEqual(notification.template_name, 'test_notification')
    
    def test_queue_notification_by_user_id(self):
        """Test queuing notification by user ID"""
        queue_notifications_to_users(
            template_name='test_notification',
            user_ids=[self.user.id],
            template_context={'recipient': self.user}
        )
        
        # Check notification was created
        notification = Notification.objects.filter(recipient=self.user).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.recipient, self.user)
    
    def test_notification_fails_without_whatsapp_contact(self):
        """Test that notification fails gracefully if user has no WhatsApp contact"""
        # Create user without WhatsApp contact
        user_no_contact = User.objects.create_user(
            username='nocontact',
            email='nocontact@example.com'
        )
        user_no_contact.groups.add(self.tech_admin_group)
        
        # Queue notification
        queue_notifications_to_users(
            template_name='test_notification',
            group_names=['Technical Admin'],
            template_context={}
        )
        
        # Get notification for user without contact
        notification = Notification.objects.filter(recipient=user_no_contact).first()
        self.assertIsNotNone(notification)
        
        # Try to dispatch - should fail gracefully
        dispatch_notification_task(notification.id)
        
        # Reload from database
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'failed')
        self.assertIn('no linked WhatsApp contact', notification.error_message)
    
    def test_notification_requires_template(self):
        """Test that notification cannot be dispatched without template"""
        # Create notification without template
        notification = Notification.objects.create(
            recipient=self.user,
            channel='whatsapp',
            status='pending',
            content='Test content',
            template_name=None  # No template
        )
        
        # Try to dispatch
        dispatch_notification_task(notification.id)
        
        # Should fail
        notification.refresh_from_db()
        self.assertEqual(notification.status, 'failed')
        self.assertIn('template_name', notification.error_message.lower())


class SignalHandlerTest(TestCase):
    """Tests to verify signal handlers are connected"""
    
    def test_signal_handlers_imported(self):
        """Test that signal handlers module can be imported"""
        try:
            import notifications.handlers
            self.assertTrue(hasattr(notifications.handlers, 'handle_failed_message_notification'))
        except ImportError:
            self.fail("Could not import notifications.handlers")
    
    def test_apps_config_ready_method(self):
        """Test that apps.py ready() method imports handlers"""
        from notifications.apps import NotificationsConfig
        config = NotificationsConfig('notifications', None)
        
        # Should not raise any errors
        try:
            config.ready()
        except Exception as e:
            self.fail(f"NotificationsConfig.ready() raised exception: {e}")


class NotificationTemplateRenderingTest(TestCase):
    """Tests for notification template rendering"""
    
    def test_template_renders_with_context(self):
        """Test that template renders correctly with provided context"""
        from notifications.utils import render_template_string
        
        template = "Hello {{ name }}, your order #{{ order_id }} is ready."
        context = {'name': 'John', 'order_id': '12345'}
        
        result = render_template_string(template, context)
        
        self.assertIn('John', result)
        self.assertIn('12345', result)
        self.assertNotIn('{{', result)
    
    def test_template_handles_missing_variables(self):
        """Test that template handles missing variables gracefully"""
        from notifications.utils import render_template_string
        
        template = "Hello {{ missing_var }}"
        context = {}
        
        result = render_template_string(template, context)
        
        # Should not raise error, missing var becomes empty string
        self.assertEqual(result.strip(), "Hello")
