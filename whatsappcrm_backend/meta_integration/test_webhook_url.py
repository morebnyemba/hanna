"""The webhook must be reachable with and without the trailing slash.

A callback URL saved in Meta without the slash used to hit APPEND_SLASH: Django
answered the POST with a 301, Meta re-sent it as a body-less GET, and every
inbound message was rejected as a failed verification.
"""
from django.test import TestCase

from .models import MetaAppConfig


class WebhookUrlTests(TestCase):
    def setUp(self):
        MetaAppConfig.objects.create(
            name='test', verify_token='tok', access_token='x',
            phone_number_id='123', waba_id='456', is_active=True,
        )

    def test_verification_works_without_trailing_slash(self):
        resp = self.client.get(
            '/crm-api/meta/webhook',
            {'hub.mode': 'subscribe', 'hub.verify_token': 'tok', 'hub.challenge': '42'},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b'42')

    def test_post_without_trailing_slash_is_not_redirected(self):
        resp = self.client.post('/crm-api/meta/webhook', data='not json', content_type='application/json')
        self.assertNotIn(resp.status_code, (301, 302, 308))
        self.assertEqual(resp.status_code, 400)
