import os
from celery import Celery


def patch_psycopg_for_gevent():
    """Make psycopg2 cooperate with gevent on the gevent-pool workers.

    psycopg2 does its network I/O in C, so without this a query that waits (on a
    lock, or just on the network) blocks the worker's only OS thread and freezes
    every greenlet in it. Two greenlets touching the same rows then deadlock in a
    way Postgres cannot see: one holds a transaction open waiting to be scheduled,
    the other blocks the thread waiting on its lock. Production hit exactly that --
    a flow worker frozen for 22h with one connection 'idle in transaction', which
    then stalled the messaging worker and the webhook behind the same contact row.

    Celery's `-P gevent` monkey-patches before this module is imported, so the
    socket check reliably tells the gevent workers apart from Daphne and the
    prefork cpu worker, which must be left alone.
    """
    try:
        from gevent import monkey
    except ImportError:
        return False
    if not monkey.is_module_patched('socket'):
        return False
    from psycogreen.gevent import patch_psycopg
    patch_psycopg()
    return True


patch_psycopg_for_gevent()

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')

# Create the Celery application instance
app = Celery('whatsappcrm_backend')

# Configure Celery using settings from Django settings.py
# The 'CELERY_' namespace means all celery settings in settings.py should start with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()

# Test task with result storage
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return {
        'status': 'success',
        'message': 'Celery is working with django-celery-results!'
    }