from celery import shared_task
from django.core.management import call_command

@shared_task
def run_fetch_mailu_attachments():
    call_command('fetch_mailu_attachments')