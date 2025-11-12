from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from .models import Notification, NotificationTemplate
from .services import (
    serialize_contact_for_template,
    serialize_flow_for_template,
    queue_notifications_to_users
)
from .tasks import serialize_user_for_template
from .utils import render_template_string
from conversations.models import Contact
from flows.models import Flow
from meta_integration.models import MetaAppConfig

User = get_user_model()


class SerializationFunctionsTests(TestCase):
    """Tests for model serialization functions used in template rendering."""

    def setUp(self):
        """Set up test data."""
        # Create a test contact
        self.contact = Contact.objects.create(
            whatsapp_id="+1234567890",
            name="Test Contact"
        )
        
        # Create a test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )

    def test_serialize_contact_for_template(self):
        """Test that contact serialization preserves necessary attributes."""
        serialized = serialize_contact_for_template(self.contact)
        
        self.assertEqual(serialized['id'], self.contact.id)
        self.assertEqual(serialized['whatsapp_id'], self.contact.whatsapp_id)
        self.assertEqual(serialized['name'], self.contact.name)
        self.assertIsInstance(serialized, dict)

    def test_serialize_contact_with_customer_profile(self):
        """Test contact serialization includes customer profile data."""
        from customer_data.models import CustomerProfile
        
        # Create a customer profile
        profile = CustomerProfile.objects.create(
            contact=self.contact,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            company="Test Company"
        )
        
        serialized = serialize_contact_for_template(self.contact)
        
        self.assertIn('customer_profile', serialized)
        self.assertEqual(serialized['customer_profile']['first_name'], "John")
        self.assertEqual(serialized['customer_profile']['last_name'], "Doe")
        self.assertEqual(serialized['customer_profile']['email'], "john.doe@example.com")
        self.assertEqual(serialized['customer_profile']['company'], "Test Company")
        self.assertEqual(serialized['customer_profile']['get_full_name'], "John Doe")

    def test_serialize_user_for_template(self):
        """Test that user serialization preserves necessary attributes."""
        serialized = serialize_user_for_template(self.user)
        
        self.assertEqual(serialized['id'], self.user.id)
        self.assertEqual(serialized['username'], self.user.username)
        self.assertEqual(serialized['email'], self.user.email)
        self.assertEqual(serialized['first_name'], self.user.first_name)
        self.assertEqual(serialized['last_name'], self.user.last_name)
        self.assertEqual(serialized['get_full_name'], "Test User")
        self.assertIsInstance(serialized, dict)

    def test_serialize_flow_for_template(self):
        """Test that flow serialization preserves necessary attributes."""
        flow = Flow.objects.create(
            name="Test Flow",
            trigger="test_trigger"
        )
        
        serialized = serialize_flow_for_template(flow)
        
        self.assertEqual(serialized['id'], flow.id)
        self.assertEqual(serialized['name'], flow.name)
        self.assertEqual(serialized['trigger'], flow.trigger)
        self.assertIsInstance(serialized, dict)


class TemplateRenderingTests(TestCase):
    """Tests for Jinja2 template rendering with serialized context."""

    def test_render_simple_template_with_contact(self):
        """Test rendering a template with contact data."""
        contact = Contact.objects.create(
            whatsapp_id="+1234567890",
            name="Alice Smith"
        )
        
        serialized_contact = serialize_contact_for_template(contact)
        template_string = "Hello {{ contact.name }}! Your ID is {{ contact.whatsapp_id }}."
        
        rendered = render_template_string(template_string, {'contact': serialized_contact})
        
        self.assertEqual(rendered, "Hello Alice Smith! Your ID is +1234567890.")

    def test_render_template_with_nested_customer_profile(self):
        """Test rendering a template with nested customer profile data."""
        from customer_data.models import CustomerProfile
        
        contact = Contact.objects.create(
            whatsapp_id="+1234567890",
            name="Test Contact"
        )
        
        profile = CustomerProfile.objects.create(
            contact=contact,
            first_name="Bob",
            last_name="Johnson",
            email="bob@example.com"
        )
        
        serialized_contact = serialize_contact_for_template(contact)
        template_string = "Hello {{ contact.customer_profile.first_name }} {{ contact.customer_profile.last_name }}! Email: {{ contact.customer_profile.email }}"
        
        rendered = render_template_string(template_string, {'contact': serialized_contact})
        
        self.assertEqual(rendered, "Hello Bob Johnson! Email: bob@example.com")

    def test_render_template_with_user_data(self):
        """Test rendering a template with user data."""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            first_name="Charlie",
            last_name="Brown"
        )
        
        serialized_user = serialize_user_for_template(user)
        template_string = "User: {{ recipient.get_full_name }} ({{ recipient.username }})"
        
        rendered = render_template_string(template_string, {'recipient': serialized_user})
        
        self.assertEqual(rendered, "User: Charlie Brown (testuser)")

    def test_render_template_with_undefined_variable(self):
        """Test that undefined variables are handled gracefully."""
        template_string = "Hello {{ contact.name }}! Your email is {{ contact.email }}."
        context = {'contact': {'name': 'Test User'}}  # email is missing
        
        rendered = render_template_string(template_string, context)
        
        # SilentUndefined should make missing variables return empty string
        self.assertEqual(rendered, "Hello Test User! Your email is .")


class NotificationTemplateIntegrationTests(TestCase):
    """Integration tests for notification template system."""

    def setUp(self):
        """Set up test data."""
        self.template = NotificationTemplate.objects.create(
            name="test_template",
            message_body="Hello {{ contact.name }}! We have a message for you.",
            body_parameters={"1": "contact.name"},
            sync_status='synced'
        )
        
        self.contact = Contact.objects.create(
            whatsapp_id="+1234567890",
            name="Test Contact"
        )
        
        self.user = User.objects.create_user(
            username="testadmin",
            email="admin@example.com",
            first_name="Admin",
            last_name="User"
        )
        
        # Link user to contact for notifications
        self.contact.user = self.user
        self.contact.save()

    @patch('notifications.services.dispatch_notification_task')
    def test_queue_notifications_with_serialized_context(self, mock_dispatch):
        """Test that queue_notifications_to_users properly serializes context."""
        mock_dispatch.delay = MagicMock()
        
        queue_notifications_to_users(
            template_name='test_template',
            user_ids=[self.user.id],
            related_contact=self.contact
        )
        
        # Check that notification was created
        notifications = Notification.objects.filter(recipient=self.user)
        self.assertEqual(notifications.count(), 1)
        
        notification = notifications.first()
        self.assertIsNotNone(notification.template_context)
        
        # Verify that contact was serialized as a dict, not a string
        self.assertIn('contact', notification.template_context)
        self.assertIsInstance(notification.template_context['contact'], dict)
        self.assertEqual(notification.template_context['contact']['name'], self.contact.name)
        
        # Verify the rendered content includes the contact name
        self.assertIn(self.contact.name, notification.content)
