"""The healthcheck endpoint the container probe depends on."""
from unittest.mock import patch

from django.test import TestCase


class HealthzTests(TestCase):
    def test_reports_ok_when_the_database_is_reachable(self):
        resp = self.client.get('/healthz/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'ok')

    def test_reports_unhealthy_when_the_database_is_not(self):
        """A probe that passes while the DB is down would defeat the point."""
        with patch('django.db.connection.cursor', side_effect=OSError('db gone')):
            resp = self.client.get('/healthz/')
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.json()['database'], 'unreachable')
