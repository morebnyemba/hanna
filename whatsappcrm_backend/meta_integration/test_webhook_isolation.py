"""
The webhook opens one transaction per change, not one per delivery.

A single delivery can carry several changes. Wrapping post() in one atomic block
meant a failure in any change rolled back the WebhookEventLog rows for all of
them, so events that had actually been handled left no record.
"""
import json
from unittest.mock import patch

from django.test import TestCase, RequestFactory

from conversations.models import Contact, Message
from meta_integration.models import MetaAppConfig, WebhookEventLog


def _change(wamid, text):
    return {
        "field": "messages",
        "value": {
            "metadata": {"phone_number_id": "pn1"},
            "contacts": [{"profile": {"name": "Tester"}}],
            "messages": [{
                "id": wamid, "from": "263771234567", "type": "text",
                "timestamp": "1700000000", "text": {"body": text},
            }],
        },
    }


def _payload(*changes):
    return {"object": "whatsapp_business_account",
            "entry": [{"id": "waba1", "changes": list(changes)}]}


class WebhookChangeIsolationTests(TestCase):
    def setUp(self):
        self.config = MetaAppConfig.objects.create(
            name='test', phone_number_id='pn1', waba_id='waba1',
            access_token='tok', verify_token='vtok', is_active=True,
        )
        self.factory = RequestFactory()

    def _post(self, payload):
        req = self.factory.post(
            '/webhook/', data=json.dumps(payload), content_type='application/json'
        )
        from meta_integration.views import MetaWebhookAPIView
        return MetaWebhookAPIView.as_view()(req)

    def test_all_changes_committed_when_all_succeed(self):
        with patch('flows.tasks.process_flow_for_message_task.delay'), \
             patch('meta_integration.tasks.send_read_receipt_task.delay'):
            resp = self._post(_payload(_change('wamid.A', 'one'), _change('wamid.B', 'two')))

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(Message.objects.filter(wamid='wamid.A').exists())
        self.assertTrue(Message.objects.filter(wamid='wamid.B').exists())

    def test_one_failing_change_does_not_discard_the_others(self):
        """The regression: a good change must survive a bad one in the same delivery."""
        from meta_integration.views import MetaWebhookAPIView
        real = MetaWebhookAPIView._handle_message

        def flaky(self, msg_data, *a, **kw):
            if msg_data.get('id') == 'wamid.BAD':
                raise RuntimeError('boom')
            return real(self, msg_data, *a, **kw)

        with patch.object(MetaWebhookAPIView, '_handle_message', flaky), \
             patch('flows.tasks.process_flow_for_message_task.delay'), \
             patch('meta_integration.tasks.send_read_receipt_task.delay'):
            resp = self._post(_payload(_change('wamid.GOOD', 'ok'), _change('wamid.BAD', 'no')))

        # The good change is committed and its log survives...
        self.assertTrue(
            Message.objects.filter(wamid='wamid.GOOD').exists(),
            "a healthy change was rolled back by an unrelated failing one",
        )
        self.assertTrue(WebhookEventLog.objects.filter(event_identifier='wamid.GOOD').exists())
        # ...the failure is recorded...
        self.assertTrue(WebhookEventLog.objects.filter(processing_status='failed').exists())
        # ...and Meta is asked to redeliver.
        self.assertEqual(resp.status_code, 500)

    def test_redelivery_is_idempotent_for_the_change_that_succeeded(self):
        """Since we return 500, Meta resends everything; that must not duplicate."""
        with patch('flows.tasks.process_flow_for_message_task.delay'), \
             patch('meta_integration.tasks.send_read_receipt_task.delay'):
            self._post(_payload(_change('wamid.A', 'one')))
            self._post(_payload(_change('wamid.A', 'one')))

        self.assertEqual(Message.objects.filter(wamid='wamid.A').count(), 1)
