# whatsappcrm_backend/analytics/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from customer_data.models import Order, JobCard, InstallationRequest, SiteAssessmentRequest, SolarCleaningRequest, Payment, CustomerProfile

def trigger_analytics_update(sender, instance, **kwargs):
    """
    Triggers a websocket update for the admin analytics dashboard.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        'admin_analytics',
        {
            'type': 'analytics_update',
        }
    )

# Register the signal handlers
post_save.connect(trigger_analytics_update, sender=Order)
post_save.connect(trigger_analytics_update, sender=JobCard)
post_save.connect(trigger_analytics_update, sender=InstallationRequest)
post_save.connect(trigger_analytics_update, sender=SiteAssessmentRequest)
post_save.connect(trigger_analytics_update, sender=SolarCleaningRequest)
post_save.connect(trigger_analytics_update, sender=Payment)
post_save.connect(trigger_analytics_update, sender=CustomerProfile)
