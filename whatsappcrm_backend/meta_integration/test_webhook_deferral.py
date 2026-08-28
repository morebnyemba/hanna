"""
Tests that the Meta webhook records and acks, rather than doing flow-engine or
order work while Meta waits.

Meta retries a webhook it considers slow, so heavy inline processing is not just
a thread-pool problem: the retry lands on top of the still-running first
delivery. Everything expensive belongs on the flow worker.
"""
from unittest.mock import patch

from django.test import TestCase

from conversations.models import Contact, Message
from meta_integration.models import MetaAppConfig, WebhookEventLog
from meta_integration.views import MetaWebhookAPIView


class WebhookDeferralTests(TestCase):
    def setUp(self):
        self.config = MetaAppConfig.objects.create(
            name='test', phone_number_id='pn1', waba_id='waba1',
            access_token='tok', verify_token='vtok', is_active=True,
        )
        self.contact = Contact.objects.create(whatsapp_id='263771234567')
        self.view = MetaWebhookAPIView()

    def _log(self):
        return WebhookEventLog.objects.create(
            app_config=self.config, event_type='message_interactive',
            event_identifier='wamid.IN1', payload={}, processing_status='pending',
        )

    # --- flow responses (nfm_reply) ---

    FLOW_MSG = {
        'id': 'wamid.IN1', 'from': '263771234567', 'type': 'interactive',
        'timestamp': '1700000000',
        'interactive': {'type': 'nfm_reply',
                        'nfm_reply': {'response_json': '{"kit_type": "x"}', 'flow_token': 't'}},
    }

    def test_flow_response_is_queued_not_processed_inline(self):
        log = self._log()
        with patch('flows.services.process_whatsapp_flow_response') as inline, \
             patch('flows.tasks.process_whatsapp_flow_response_task.delay') as queued:
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_flow_response(self.FLOW_MSG, self.contact, self.config, log)

        self.assertFalse(inline.called, "flow engine ran on the webhook request path")
        self.assertTrue(queued.called, "flow response was never queued")

        msg = Message.objects.get(wamid='wamid.IN1')
        queued.assert_called_once_with(msg.id, log.id)

    def test_duplicate_flow_response_is_not_queued_twice(self):
        """Meta redelivering a submitted form must not re-run it."""
        with patch('flows.tasks.process_whatsapp_flow_response_task.delay') as queued:
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_flow_response(self.FLOW_MSG, self.contact, self.config, self._log())
            first = queued.call_count
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_flow_response(self.FLOW_MSG, self.contact, self.config, self._log())
            self.assertEqual(queued.call_count, first, "duplicate delivery was queued again")

    def test_broker_failure_does_not_raise_into_the_webhook(self):
        """A broker outage must not become a 500 and a full Meta redelivery."""
        log = self._log()
        with patch('flows.tasks.process_whatsapp_flow_response_task.delay',
                   side_effect=OSError('redis down')):
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_flow_response(self.FLOW_MSG, self.contact, self.config, log)
        # The message is still recorded, so the work is recoverable.
        self.assertTrue(Message.objects.filter(wamid='wamid.IN1').exists())

    # --- catalog orders ---

    ORDER_MSG = {
        'id': 'wamid.ORDER1', 'from': '263771234567', 'type': 'order',
        'order': {'catalog_id': 'c1', 'product_items': [
            {'product_retailer_id': 'p1', 'quantity': 1, 'item_price': 10, 'currency': 'USD'}]},
    }

    def test_catalog_order_is_queued_not_processed_inline(self):
        log = self._log()
        with patch('flows.services.process_order_from_catalog') as inline, \
             patch('flows.tasks.process_catalog_order_task.delay') as queued:
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_order_message(self.ORDER_MSG, self.contact, self.config, log)

        self.assertFalse(inline.called, "order processing ran on the webhook request path")
        msg = Message.objects.get(wamid='wamid.ORDER1')
        queued.assert_called_once_with(msg.id, log.id)

    def test_duplicate_order_is_not_queued_twice(self):
        with patch('flows.tasks.process_catalog_order_task.delay') as queued:
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_order_message(self.ORDER_MSG, self.contact, self.config, self._log())
            first = queued.call_count
            with self.captureOnCommitCallbacks(execute=True):
                self.view._handle_order_message(self.ORDER_MSG, self.contact, self.config, self._log())
            self.assertEqual(queued.call_count, first, "duplicate order was queued again")


class DeferredTaskTests(TestCase):
    """The other half: the queued task must do the work and close out the log."""

    def setUp(self):
        self.config = MetaAppConfig.objects.create(
            name='test', phone_number_id='pn1', waba_id='waba1',
            access_token='tok', verify_token='vtok', is_active=True,
        )
        self.contact = Contact.objects.create(whatsapp_id='263771234567')
        self.log = WebhookEventLog.objects.create(
            app_config=self.config, event_type='message_interactive',
            event_identifier='wamid.IN1', payload={},
            processing_status='processing_queued',
        )
        self.msg = Message.objects.create(
            contact=self.contact, app_config=self.config, direction='in',
            message_type='interactive', wamid='wamid.IN1',
            content_payload={'interactive': {'type': 'nfm_reply'}}, status='delivered',
        )

    def test_flow_response_task_runs_engine_and_finalises_log(self):
        from flows.tasks import process_whatsapp_flow_response_task

        with patch('flows.services.process_whatsapp_flow_response',
                   return_value=(True, 'ok')) as processor, \
             patch('flows.tasks.process_flow_for_message_task') as continuation:
            process_whatsapp_flow_response_task(self.msg.id, self.log.id)

        self.assertTrue(processor.called, "the deferred work never ran")
        continuation.assert_called_once_with(self.msg.id)
        self.log.refresh_from_db()
        self.assertEqual(self.log.processing_status, 'processed')

    def test_flow_response_failure_is_recorded_and_stops_the_chain(self):
        from flows.tasks import process_whatsapp_flow_response_task

        with patch('flows.services.process_whatsapp_flow_response',
                   return_value=(False, 'no matching flow')), \
             patch('flows.tasks.process_flow_for_message_task') as continuation:
            process_whatsapp_flow_response_task(self.msg.id, self.log.id)

        self.assertFalse(continuation.called, "flow continued despite a failed response")
        self.log.refresh_from_db()
        self.assertEqual(self.log.processing_status, 'error')
        self.assertIn('no matching flow', self.log.processing_notes)

    def test_catalog_order_task_finalises_log(self):
        from flows.tasks import process_catalog_order_task

        with patch('flows.services.process_order_from_catalog',
                   return_value=(True, 'Order ORD-1 created.')) as processor:
            process_catalog_order_task(self.msg.id, self.log.id)

        self.assertTrue(processor.called)
        self.log.refresh_from_db()
        self.assertEqual(self.log.processing_status, 'processed')
        self.assertIn('ORD-1', self.log.processing_notes)

    def test_missing_message_is_recorded_rather_than_crashing(self):
        from flows.tasks import process_catalog_order_task

        process_catalog_order_task(999999, self.log.id)
        self.log.refresh_from_db()
        self.assertEqual(self.log.processing_status, 'error')
