"""psycopg2 must yield to gevent on the gevent-pool workers, and only there.

Each case runs in a fresh interpreter because gevent monkey-patching is
process-wide and irreversible.
"""
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BACKEND_DIR = Path(__file__).resolve().parent.parent

PROBE = """
{prelude}
import psycopg2.extensions
import whatsappcrm_backend.celery  # patches at import time when running under gevent
print(psycopg2.extensions.get_wait_callback() is not None)
"""


def _wait_callback_installed(prelude):
    result = subprocess.run(
        [sys.executable, '-c', PROBE.format(prelude=prelude)],
        cwd=BACKEND_DIR, capture_output=True, text=True, timeout=60,
    )
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip().splitlines()[-1] == 'True'


class PsycopgGeventPatchTests(SimpleTestCase):
    def test_gevent_worker_gets_cooperative_psycopg(self):
        # What `celery worker -P gevent` does before importing the app.
        self.assertTrue(_wait_callback_installed('from gevent import monkey; monkey.patch_all()'))

    def test_non_gevent_processes_are_left_alone(self):
        # Daphne and the prefork cpu worker: a gevent wait callback there would
        # be wrong, since nothing runs the gevent hub.
        self.assertFalse(_wait_callback_installed(''))
