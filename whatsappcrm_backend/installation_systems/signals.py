"""
Signal handlers for installation_systems app.

Automatically creates InstallationSystemRecord when InstallationRequest is saved.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from customer_data.models import InstallationRequest
from .models import InstallationSystemRecord
from decimal import Decimal

logger = logging.getLogger(__name__)


@receiver(post_save, sender=InstallationRequest)
def create_installation_system_record(sender, instance, created, **kwargs):
    """
    Signal handler to auto-create InstallationSystemRecord when InstallationRequest is created.
    
    Maps InstallationRequest fields to InstallationSystemRecord fields:
    - customer -> customer
    - associated_order -> order
    - installation_type -> installation_type
    - address -> installation_address
    - location_latitude/longitude -> latitude/longitude
    - technicians -> technicians (ManyToMany, set after creation)
    """
    # Only create ISR for new InstallationRequests that don't already have one
    if created and not hasattr(instance, 'installation_system_record'):
        try:
            # Map installation_type
            installation_type = instance.installation_type
            
            # Handle legacy types
            if installation_type in ['residential', 'commercial']:
                # Default to solar for legacy types
                installation_type = 'solar'
                system_classification = instance.installation_type  # residential or commercial
            else:
                # Use the new installation types
                system_classification = 'residential'  # default
            
            # Determine capacity unit based on installation type
            if installation_type in ['solar', 'hybrid']:
                capacity_unit = 'kW'
            elif installation_type == 'starlink':
                capacity_unit = 'Mbps'
            else:
                capacity_unit = 'units'
            
            # Create the ISR
            isr = InstallationSystemRecord.objects.create(
                installation_request=instance,
                customer=instance.customer,
                order=instance.associated_order,
                installation_type=installation_type,
                system_classification=system_classification,
                capacity_unit=capacity_unit,
                installation_status='pending',
                installation_address=instance.address or '',
                latitude=instance.location_latitude or instance.latitude,
                longitude=instance.location_longitude or instance.longitude,
            )
            
            # Copy technicians (ManyToMany relationship)
            if instance.technicians.exists():
                isr.technicians.set(instance.technicians.all())
            
            logger.info(
                f"Created InstallationSystemRecord {isr.id} for InstallationRequest {instance.id} "
                f"(type: {installation_type}, customer: {instance.customer})"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create InstallationSystemRecord for InstallationRequest {instance.id}: {e}",
                exc_info=True
            )


@receiver(post_save, sender=InstallationRequest)
def update_installation_system_record_status(sender, instance, created, **kwargs):
    """
    Signal handler to sync InstallationRequest status changes to InstallationSystemRecord.
    
    Maps statuses:
    - pending -> pending
    - scheduled -> pending
    - in_progress -> in_progress
    - completed -> commissioned
    - cancelled -> decommissioned
    """
    # Only update if ISR exists and this is an update (not creation)
    if not created and hasattr(instance, 'installation_system_record'):
        try:
            isr = instance.installation_system_record
            
            # Map status
            status_mapping = {
                'pending': 'pending',
                'scheduled': 'pending',
                'in_progress': 'in_progress',
                'completed': 'commissioned',
                'cancelled': 'decommissioned',
            }
            
            new_status = status_mapping.get(instance.status, 'pending')
            
            if isr.installation_status != new_status:
                isr.installation_status = new_status
                isr.save(update_fields=['installation_status', 'updated_at'])
                
                logger.info(
                    f"Updated InstallationSystemRecord {isr.id} status to {new_status} "
                    f"(from InstallationRequest {instance.id} status {instance.status})"
                )
        except Exception as e:
            logger.error(
                f"Failed to update InstallationSystemRecord status for InstallationRequest {instance.id}: {e}",
                exc_info=True
            )
