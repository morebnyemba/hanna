from celery.schedules import schedule
app.conf.beat_schedule = {
    'fetch-mailu-attachments-every-20s': {
        'task': 'whatsappcrm_backend.periodic_tasks.run_fetch_mailu_attachments',
        'schedule': 20.0,
    },
}
import os
from celery import Celery

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