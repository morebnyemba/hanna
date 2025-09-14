from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Notification(models.Model):
    """
    Represents a notification to be sent to a system user (admin/agent).
    """
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    channel = models.CharField(_("Channel"), max_length=20, default='whatsapp')
    status = models.CharField(
        _("Status"), max_length=20,
        choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed'), ('read', 'Read')],
        default='pending', db_index=True
    )
    content = models.TextField(_("Content"))
    related_contact = models.ForeignKey('conversations.Contact', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_notifications')
    related_flow = models.ForeignKey('flows.Flow', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_notifications')
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Notification for {self.recipient.username} ({self.status})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("System Notification")
        verbose_name_plural = _("System Notifications")