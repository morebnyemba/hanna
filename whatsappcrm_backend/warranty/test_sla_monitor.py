"""monitor_sla_compliance: SLA alerts reach staff as WhatsApp template notifications.

The task used to import a NotificationService that never existed, so it
crashed on every hourly run and no SLA alert was ever sent.
"""
import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.utils import timezone

from notifications.management.commands.seed_notification_templates import NOTIFICATION_TEMPLATES
from notifications.models import Notification, NotificationTemplate
from warranty.models import SLAStatus, SLAThreshold
from warranty.tasks import monitor_sla_compliance

User = get_user_model()


class MonitorSlaComplianceTests(TestCase):
    def setUp(self):
        definition = next(t for t in NOTIFICATION_TEMPLATES if t['name'] == 'pfungwa_sla_alert')
        NotificationTemplate.objects.create(
            name=definition['name'],
            message_body=definition['message_body'],
            body_parameters=definition['body_parameters'],
        )
        self.staff = User.objects.create_user(username='tech', password='x')
        self.staff.groups.add(Group.objects.create(name='Technical Admin'))
        self.threshold = SLAThreshold.objects.create(
            name='Install SLA', request_type='installation',
            response_time_hours=24, resolution_time_hours=72,
            notification_threshold_percent=80,
        )

    def _sla_status(self, created_hours_ago):
        created = timezone.now() - timedelta(hours=created_hours_ago)
        # Any model works as the tracked request; the task only reads its pk.
        return SLAStatus.objects.create(
            content_type=ContentType.objects.get_for_model(User),
            object_id=str(self.staff.pk),
            sla_threshold=self.threshold,
            request_created_at=created,
            response_time_deadline=created + timedelta(hours=24),
            resolution_time_deadline=created + timedelta(hours=72),
        )

    @patch('notifications.services.dispatch_notification_task')
    def test_breached_request_notifies_staff_with_template(self, _dispatch):
        sla_status = self._sla_status(created_hours_ago=30)  # response deadline passed

        monitor_sla_compliance()

        notification = Notification.objects.get(recipient=self.staff)
        self.assertEqual(notification.template_name, 'pfungwa_sla_alert')
        self.assertIn(f'Installation Request #{self.staff.pk}', notification.content)
        self.assertIn('SLA Breached', notification.content)
        # Stored in a JSONField and rendered into Meta body parameters: must be plain strings.
        json.dumps(notification.template_context)
        self.assertRegex(notification.template_context['response_deadline'], r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$')
        sla_status.refresh_from_db()
        self.assertIsNotNone(sla_status.last_notification_sent)

    @patch('notifications.services.dispatch_notification_task')
    def test_compliant_request_sends_nothing(self, _dispatch):
        self._sla_status(created_hours_ago=1)

        monitor_sla_compliance()

        self.assertFalse(Notification.objects.exists())

    @patch('notifications.services.dispatch_notification_task')
    def test_recently_alerted_breach_is_not_repeated(self, _dispatch):
        self._sla_status(created_hours_ago=30)

        monitor_sla_compliance()
        monitor_sla_compliance()

        self.assertEqual(Notification.objects.count(), 1)
