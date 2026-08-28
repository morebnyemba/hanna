"""
Regression tests for the sequential-delivery gate in send_whatsapp_message_task.

The gate exists to preserve reply ordering. It must never turn into a delivery
decision: before this was fixed, a lagging delivery receipt made every message
from the third onwards in a flow burst exhaust its retry budget while merely
*waiting*, and get marked 'failed' without the Meta API ever being called.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from conversations.models import Contact, Message
from meta_integration.models import MetaAppConfig
from meta_integration.tasks import (
    ORDERING_WAIT_BUDGET_SECONDS,
    send_whatsapp_message_task,
)

SEND_OK = {'messages': [{'id': 'wamid.TEST'}]}


class SendOrderingGateTests(TestCase):
    def setUp(self):
        self.config = MetaAppConfig.objects.create(
            name='test', phone_number_id='pn1', waba_id='waba1',
            access_token='tok', verify_token='vtok', is_active=True,
        )
        self.contact = Contact.objects.create(whatsapp_id='263771234567')

    def _msg(self, status='pending_dispatch', **kw):
        return Message.objects.create(
            contact=self.contact, app_config=self.config, direction='out',
            message_type='text', content_payload={'body': 'hi'}, status=status, **kw
        )

    def _run(self, msg):
        send_whatsapp_message_task.apply(args=[msg.id, self.config.id])
        msg.refresh_from_db()
        return msg

    @patch('meta_integration.tasks.send_whatsapp_message', return_value=SEND_OK)
    def test_sends_when_nothing_precedes_it(self, mock_send):
        msg = self._run(self._msg())
        self.assertEqual(msg.status, 'sent')
        self.assertTrue(mock_send.called)

    @patch('meta_integration.tasks.send_whatsapp_message', return_value=SEND_OK)
    def test_message_past_ordering_budget_is_sent_not_failed(self, mock_send):
        """The core regression: a stalled predecessor must not drop the message."""
        # A predecessor stuck at 'sent' -- its delivery receipt never arrived.
        self._msg(status='sent', status_timestamp=timezone.now())
        # This message has been waiting longer than the ordering budget allows.
        old = timezone.now() - timedelta(seconds=ORDERING_WAIT_BUDGET_SECONDS + 5)
        msg = self._run(self._msg(timestamp=old))

        self.assertEqual(msg.status, 'sent', "message was dropped instead of sent")
        self.assertTrue(mock_send.called, "Meta API was never called")

    @patch('meta_integration.tasks.send_whatsapp_message', return_value=SEND_OK)
    def test_holds_behind_a_recently_sent_predecessor(self, mock_send):
        """Ordering is still enforced while the message is inside its budget.

        Asserted against the gate's decision (did it ask to retry?) rather than
        by running the task eagerly: under CELERY_TASK_ALWAYS_EAGER, self.retry()
        re-runs the task inline with no countdown, so it would spin through the
        whole ordering budget in microseconds and send regardless.
        """
        self._msg(status='sent', status_timestamp=timezone.now())
        msg = self._msg()

        with patch.object(send_whatsapp_message_task, 'retry',
                          side_effect=RuntimeError('retry-requested')) as mock_retry:
            with self.assertRaisesMessage(RuntimeError, 'retry-requested'):
                send_whatsapp_message_task.apply(
                    args=[msg.id, self.config.id], throw=True
                ).get()

        self.assertTrue(mock_retry.called, "gate should have held the message back")
        self.assertFalse(mock_send.called, "message was sent out of order")
        msg.refresh_from_db()
        self.assertNotEqual(msg.status, 'failed',
                            "an ordering wait must never fail a message")

    @patch('meta_integration.tasks.send_whatsapp_message', return_value=SEND_OK)
    def test_delivered_predecessor_does_not_hold_the_queue(self, mock_send):
        self._msg(status='delivered', status_timestamp=timezone.now())
        msg = self._run(self._msg())
        self.assertEqual(msg.status, 'sent')
        self.assertTrue(mock_send.called)
