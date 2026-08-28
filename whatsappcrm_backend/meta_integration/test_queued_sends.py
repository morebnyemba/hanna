"""
Tests that request-path handlers queue outgoing WhatsApp messages instead of
making a blocking Meta API call.

Daphne serves every synchronous Django view from one small shared thread pool,
so a handler that sits in requests.post() for up to 20s occupies a slot in that
pool -- and, in the webhook's case, holds an open DB transaction while it does.
A few concurrent ones took the whole site down.
"""
from unittest.mock import patch

from django.test import TestCase

from conversations.models import Contact, Message
from meta_integration.models import MetaAppConfig
from meta_integration.utils import queue_whatsapp_message


class QueueWhatsAppMessageTests(TestCase):
    def setUp(self):
        self.config = MetaAppConfig.objects.create(
            name='test', phone_number_id='pn1', waba_id='waba1',
            access_token='tok', verify_token='vtok', is_active=True,
        )
        self.contact = Contact.objects.create(whatsapp_id='263771234567')

    @patch('meta_integration.utils.requests.post')
    def test_queues_without_network_io(self, mock_post):
        msg = queue_whatsapp_message(
            contact=self.contact, message_type='text',
            data={'body': 'hello'}, config=self.config,
        )

        self.assertIsNotNone(msg)
        self.assertFalse(mock_post.called, "handler made a blocking Meta API call")
        msg.refresh_from_db()
        self.assertEqual(msg.status, 'pending_dispatch')
        self.assertEqual(msg.direction, 'out')
        self.assertEqual(msg.content_payload, {'body': 'hello'})

    @patch('meta_integration.utils.requests.post')
    def test_queued_message_is_dispatched_on_commit(self, mock_post):
        """The Celery task must be dispatched, and only after the commit."""
        with patch('meta_integration.tasks.send_whatsapp_message_task.delay') as mock_delay:
            with self.captureOnCommitCallbacks(execute=True):
                msg = queue_whatsapp_message(
                    contact=self.contact, message_type='text',
                    data={'body': 'hi'}, config=self.config,
                )
                self.assertFalse(mock_delay.called, "dispatched before commit")
            mock_delay.assert_called_once_with(msg.id, self.config.id)
        self.assertFalse(mock_post.called)

    @patch('meta_integration.utils.requests.post')
    def test_broker_failure_does_not_break_the_caller(self, mock_post):
        """A wedged broker must not turn a webhook into a 500 and a Meta retry."""
        with patch('meta_integration.tasks.send_whatsapp_message_task.delay',
                   side_effect=OSError('redis down')):
            with self.captureOnCommitCallbacks(execute=True):
                msg = queue_whatsapp_message(
                    contact=self.contact, message_type='text',
                    data={'body': 'hi'}, config=self.config,
                )
        # The row survives for re-dispatch rather than the message being lost.
        msg.refresh_from_db()
        self.assertEqual(msg.status, 'pending_dispatch')
