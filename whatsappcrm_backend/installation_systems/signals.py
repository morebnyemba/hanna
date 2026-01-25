"""
Signal handlers for installation_systems app.

Automatically creates InstallationSystemRecord when InstallationRequest is saved.
Also auto-creates checklist entries when technicians are assigned to installations.
"""

import logging
from django.db import models
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from customer_data.models import InstallationRequest
from warranty.models import Technician
from .models import InstallationSystemRecord, CommissioningChecklistTemplate, InstallationChecklistEntry
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
                latitude=instance.location_latitude or getattr(instance, 'latitude', None),
                longitude=instance.location_longitude or getattr(instance, 'longitude', None),
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


def create_checklists_for_installation(isr):
    """
    Helper function to create checklist entries for an InstallationSystemRecord.
    Creates checklists based on applicable templates for the installation type.
    
    Template matching logic:
    - Templates with installation_type matching the ISR's type are applied
    - Templates with installation_type=NULL are treated as universal templates 
      that apply to all installation types
    """
    try:
        # Find applicable checklist templates
        # Templates with null installation_type are universal and apply to all types
        templates = CommissioningChecklistTemplate.objects.filter(
            is_active=True
        ).filter(
            # Match templates for this installation type OR universal templates (null type)
            models.Q(installation_type=isr.installation_type) | 
            models.Q(installation_type__isnull=True)
        )
        
        if not templates.exists():
            logger.warning(
                f"No active checklist templates found for installation type: {isr.installation_type}"
            )
            return []
        
        created_entries = []
        for template in templates:
            # Check if checklist entry already exists for this template
            existing = InstallationChecklistEntry.objects.filter(
                installation_record=isr,
                template=template
            ).exists()
            
            if not existing:
                # Get technician from the ISR if available
                technician = isr.technicians.first() if isr.technicians.exists() else None
                
                entry = InstallationChecklistEntry.objects.create(
                    installation_record=isr,
                    template=template,
                    technician=technician,
                    completed_items={},
                    completion_status='not_started',
                    completion_percentage=0,
                )
                created_entries.append(entry)
                logger.info(
                    f"Created checklist entry {entry.id} for ISR {isr.id} "
                    f"using template '{template.name}' (type: {template.checklist_type})"
                )
        
        return created_entries
        
    except Exception as e:
        logger.error(
            f"Failed to create checklists for ISR {isr.id}: {e}",
            exc_info=True
        )
        return []


@receiver(post_save, sender=InstallationSystemRecord)
def auto_create_checklists_on_isr_create(sender, instance, created, **kwargs):
    """
    Signal handler to auto-create checklist entries when InstallationSystemRecord is created.
    """
    if created:
        create_checklists_for_installation(instance)


@receiver(m2m_changed, sender=InstallationSystemRecord.technicians.through)
def auto_create_checklists_on_technician_assigned(sender, instance, action, **kwargs):
    """
    Signal handler to create checklists when technicians are assigned to an installation.
    This ensures checklists are created even if they weren't created during initial ISR creation.
    """
    if action in ['post_add']:
        # Check if checklists already exist
        existing_checklists = InstallationChecklistEntry.objects.filter(
            installation_record=instance
        ).count()
        
        if existing_checklists == 0:
            create_checklists_for_installation(instance)
        else:
            # Update technician assignment on existing checklists if not set
            technician = instance.technicians.first() if instance.technicians.exists() else None
            if technician:
                InstallationChecklistEntry.objects.filter(
                    installation_record=instance,
                    technician__isnull=True
                ).update(technician=technician)


@receiver(m2m_changed, sender=InstallationRequest.technicians.through)
def sync_technicians_to_isr_and_create_checklists(sender, instance, action, pk_set, **kwargs):
    """
    Signal handler to sync technician assignments from InstallationRequest to ISR.
    Also ensures checklists are created when technicians are assigned.
    
    This handles the case where technicians are assigned via InstallationRequest
    rather than directly on the InstallationSystemRecord.
    """
    if action in ['post_add']:
        # Check if this InstallationRequest has an associated ISR
        if hasattr(instance, 'installation_system_record'):
            isr = instance.installation_system_record
            
            # Sync technicians to ISR
            for tech_id in pk_set:
                try:
                    technician = Technician.objects.get(pk=tech_id)
                    if not isr.technicians.filter(pk=tech_id).exists():
                        isr.technicians.add(technician)
                        logger.info(
                            f"Synced technician {technician} to ISR {isr.id} from InstallationRequest"
                        )
                except Technician.DoesNotExist:
                    pass
            
            # Check if checklists exist, create if not
            existing_checklists = InstallationChecklistEntry.objects.filter(
                installation_record=isr
            ).count()
            
            if existing_checklists == 0:
                create_checklists_for_installation(isr)
                logger.info(
                    f"Created checklists for ISR {isr.id} after technician assigned via InstallationRequest"
                )
            else:
                # Update technician assignment on existing checklists if not set
                technician = isr.technicians.first() if isr.technicians.exists() else None
                if technician:
                    updated = InstallationChecklistEntry.objects.filter(
                        installation_record=isr,
                        technician__isnull=True
                    ).update(technician=technician)
                    if updated:
                        logger.info(
                            f"Assigned technician {technician} to {updated} existing checklists for ISR {isr.id}"
                        )
