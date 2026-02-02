"""
Signal handlers for installation_systems app.

Automatically creates InstallationSystemRecord when InstallationRequest is saved.
Also auto-creates checklist entries when technicians are assigned to installations.
"""

import logging
from django.db import models, transaction
from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from customer_data.models import InstallationRequest
from warranty.models import Technician
from .models import InstallationSystemRecord, CommissioningChecklistTemplate, InstallationChecklistEntry, InstallerPayout
from notifications.services import queue_notifications_to_users
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


@receiver(post_save, sender=InstallationSystemRecord)
def send_installation_status_notifications(sender, instance, created, **kwargs):
    """
    Send notifications when installation status changes to specific states.
    """
    if not created:
        # Check if status changed to commissioned (installation complete)
        if instance.installation_status == 'commissioned':
            customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
            if customer_contact:
                # Build warranty summary
                warranty_list = []
                for warranty in instance.warranties.all():
                    warranty_list.append(f"- {warranty.serialized_item.product.name}: {warranty.end_date.strftime('%Y-%m-%d')}")
                warranty_summary = '\n'.join(warranty_list) if warranty_list else 'No warranties registered yet'
                
                context = {
                    'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                    'installation_type': instance.get_installation_type_display(),
                    'system_size': str(instance.system_size) if instance.system_size else 'N/A',
                    'isr_id': str(instance.id),
                    'warranty_summary': warranty_summary,
                }
                transaction.on_commit(
                    lambda: queue_notifications_to_users(
                        template_name='pfungwa_installation_complete',
                        contact_ids=[customer_contact.id],
                        related_contact=customer_contact,
                        template_context=context
                    )
                )
                logger.info(f"Queued installation complete notification for ISR {instance.id}.")


@receiver(m2m_changed, sender=InstallationSystemRecord.technicians.through)
def send_technician_assignment_notification(sender, instance, action, pk_set, **kwargs):
    """
    Send notification to technician when they are assigned to an installation.
    """
    if action == 'post_add' and pk_set:
        customer_contact = instance.customer.contact if instance.customer and hasattr(instance.customer, 'contact') else None
        
        for tech_id in pk_set:
            try:
                technician = Technician.objects.get(pk=tech_id)
                tech_contact = technician.user.customer_profile.contact if hasattr(technician.user, 'customer_profile') and hasattr(technician.user.customer_profile, 'contact') else None
                
                if tech_contact:
                    context = {
                        'technician_name': technician.user.get_full_name() or technician.user.username,
                        'customer_name': instance.customer.get_full_name() if instance.customer else 'Customer',
                        'installation_address': instance.installation_address or 'Address not specified',
                        'installation_date': instance.installation_date.strftime('%Y-%m-%d') if instance.installation_date else 'To be scheduled',
                        'system_size': str(instance.system_size) if instance.system_size else 'N/A',
                        'installation_type': instance.get_installation_type_display(),
                        'isr_id': str(instance.id),
                    }
                    
                    # Use a helper function to capture context values correctly
                    def send_notification(contact_id, notification_context):
                        queue_notifications_to_users(
                            template_name='pfungwa_technician_job_assigned',
                            contact_ids=[contact_id],
                            related_contact=tech_contact,
                            template_context=notification_context
                        )
                    
                    transaction.on_commit(lambda ctx=context, cid=tech_contact.id: send_notification(cid, ctx))
                    logger.info(f"Queued technician assignment notification for technician {tech_id} on ISR {instance.id}.")
            except Technician.DoesNotExist:
                logger.warning(f"Technician {tech_id} not found when trying to send assignment notification.")


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


@receiver(post_save, sender=InstallerPayout)
def send_payout_status_notifications(sender, instance, created, **kwargs):
    """
    Send notifications to technician when payout status changes to approved or paid.
    """
    if not created:
        # Get technician contact
        tech_contact = None
        if instance.technician and hasattr(instance.technician, 'user'):
            user = instance.technician.user
            if hasattr(user, 'customer_profile') and hasattr(user.customer_profile, 'contact'):
                tech_contact = user.customer_profile.contact
        
        if tech_contact:
            # Notification when payout is approved
            if instance.status == InstallerPayout.PayoutStatus.APPROVED:
                # Count installations in this payout
                installation_count = instance.installations.count()
                
                context = {
                    'technician_name': instance.technician.user.get_full_name() or instance.technician.user.username,
                    'payout_id': str(instance.id),
                    'payout_amount': str(instance.payout_amount),
                    'installation_count': str(installation_count),
                }
                
                transaction.on_commit(
                    lambda: queue_notifications_to_users(
                        template_name='pfungwa_payout_approved',
                        contact_ids=[tech_contact.id],
                        related_contact=tech_contact,
                        template_context=context
                    )
                )
                logger.info(f"Queued payout approval notification for payout {instance.id}.")
            
            # Notification when payout is paid
            elif instance.status == InstallerPayout.PayoutStatus.PAID:
                context = {
                    'technician_name': instance.technician.user.get_full_name() or instance.technician.user.username,
                    'payout_id': str(instance.id),
                    'payout_amount': str(instance.payout_amount),
                    'payment_reference': str(instance.id),  # Full UUID for uniqueness
                }
                
                transaction.on_commit(
                    lambda: queue_notifications_to_users(
                        template_name='pfungwa_payout_paid',
                        contact_ids=[tech_contact.id],
                        related_contact=tech_contact,
                        template_context=context
                    )
                )
                logger.info(f"Queued payout paid notification for payout {instance.id}.")
