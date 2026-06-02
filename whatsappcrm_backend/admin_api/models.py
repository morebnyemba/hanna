# whatsappcrm_backend/admin_api/models.py
"""
Models for Admin API - Task monitoring and dead letter queue.
"""

from django.db import models
from django.utils import timezone


class FailedTask(models.Model):
    """
    Dead letter queue for permanently failed Celery tasks.
    Records are created automatically when tasks using BaseTaskWithRetry
    exhaust all retries.
    """
    STATUS_CHOICES = [
        ('failed', 'Failed'),
        ('retried', 'Manually Retried'),
        ('resolved', 'Resolved'),
    ]

    task_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="The Celery task UUID."
    )
    task_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The full task name (e.g., 'meta_integration.tasks.send_whatsapp_message_task')."
    )
    args = models.JSONField(
        default=list,
        blank=True,
        help_text="Positional arguments the task was called with."
    )
    kwargs = models.JSONField(
        default=dict,
        blank=True,
        help_text="Keyword arguments the task was called with."
    )
    exception_type = models.CharField(
        max_length=255,
        help_text="The type of exception that caused the failure."
    )
    exception_message = models.TextField(
        help_text="The exception message."
    )
    traceback = models.TextField(
        blank=True,
        default='',
        help_text="The full traceback of the exception."
    )
    retries = models.PositiveIntegerField(
        default=0,
        help_text="Number of retries attempted before final failure."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='failed',
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"FailedTask {self.task_name} [{self.task_id}] at {self.created_at}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Failed Task"
        verbose_name_plural = "Failed Tasks"
        indexes = [
            models.Index(fields=['task_name', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]


class TaskProgress(models.Model):
    """
    Tracks the progress of long-running Celery tasks.
    Tasks can update their progress via TaskProgress.objects.update_progress().
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('started', 'Started'),
        ('progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    task_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="The Celery task UUID."
    )
    task_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The full task name."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
    )
    progress_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="Progress percentage (0-100)."
    )
    message = models.TextField(
        blank=True,
        default='',
        help_text="Human-readable status message."
    )
    result = models.JSONField(
        null=True,
        blank=True,
        help_text="Task result data (set on completion)."
    )
    error = models.TextField(
        blank=True,
        default='',
        help_text="Error details if the task failed."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TaskProgress {self.task_name} [{self.task_id}] - {self.status} ({self.progress_percent}%)"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task Progress"
        verbose_name_plural = "Task Progress"
        indexes = [
            models.Index(fields=['task_name', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
