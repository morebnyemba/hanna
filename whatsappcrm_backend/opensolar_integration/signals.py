# whatsappcrm_backend/opensolar_integration/signals.py

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from customer_data.models import InstallationRequest
from .models import OpenSolarConfig, OpenSolarProject
from .tasks import sync_installation_to_opensolar

logger = logging.getLogger(__name__)


@receiver(post_save, sender=InstallationRequest)
def auto_sync_installation_to_opensolar(sender, instance, created, **kwargs):
    """
    Automatically sync new installation requests to OpenSolar if enabled.
    """
    # Check if auto-sync is enabled
    try:
        config = OpenSolarConfig.objects.filter(is_active=True).first()
        if not config or not config.auto_sync_enabled:
            return
    except OpenSolarConfig.DoesNotExist:
        return
    
    # Only sync solar installation types
    if instance.installation_type not in ['solar', 'hybrid']:
        return
    
    # Only sync if not already synced or if updated
    try:
        opensolar_project = OpenSolarProject.objects.get(
            installation_request=instance
        )
        # If already synced successfully, skip
        if opensolar_project.sync_status == 'synced' and not created:
            # Could trigger update here if needed
            pass
    except OpenSolarProject.DoesNotExist:
        # New installation request, queue for sync
        logger.info(f"Queueing installation request {instance.id} for OpenSolar sync")
        sync_installation_to_opensolar.delay(instance.id)
