import os
import logging
from celery import Celery, Task

logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsappcrm_backend.settings')

# Create the Celery application instance
app = Celery('whatsappcrm_backend')

# Configure Celery using settings from Django settings.py
# The 'CELERY_' namespace means all celery settings in settings.py should start with CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps
app.autodiscover_tasks()


class BaseTaskWithRetry(Task):
    """
    Base Celery task class with exponential backoff retry strategy.

    Usage:
        @shared_task(base=BaseTaskWithRetry, max_retries=5)
        def my_task():
            ...

    Retry delays (default): 60s, 120s, 240s, 480s, 960s, ...
    """
    autoretry_for = (Exception,)
    max_retries = 5
    retry_backoff = 60         # Base delay in seconds
    retry_backoff_max = 3600   # Maximum delay cap (1 hour)
    retry_jitter = True        # Add randomness to prevent thundering herd

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log failed tasks and store them in the dead letter queue."""
        logger.error(
            "Task %s[%s] failed permanently after %d retries: %s",
            self.name, task_id, self.request.retries, exc,
        )
        try:
            from admin_api.models import FailedTask
            FailedTask.objects.create(
                task_id=task_id,
                task_name=self.name,
                args=list(args) if args else [],
                kwargs=dict(kwargs) if kwargs else {},
                exception_type=type(exc).__name__,
                exception_message=str(exc)[:1000],
                traceback=str(einfo)[:5000] if einfo else '',
                retries=self.request.retries,
            )
        except Exception as store_exc:
            logger.error(
                "Failed to store dead letter for task %s[%s]: %s",
                self.name, task_id, store_exc,
            )
        super().on_failure(exc, task_id, args, kwargs, einfo)


# Test task with result storage
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
    return {
        'status': 'success',
        'message': 'Celery is working with django-celery-results!'
    }