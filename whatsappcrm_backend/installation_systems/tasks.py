"""
Celery tasks for installation systems.
Handles background jobs for payouts, notifications, and integrations.
"""
import logging
from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


@shared_task(queue='celery')
def sync_payout_to_zoho(payout_id):
    """
    Sync approved payout to Zoho as a bill/expense.
    
    Args:
        payout_id: UUID of the InstallerPayout to sync
        
    Returns:
        dict: Sync result with status and details
    """
    from .models import InstallerPayout
    from integrations.utils import ZohoClient
    
    try:
        payout = InstallerPayout.objects.get(id=payout_id)
    except InstallerPayout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
        return {'success': False, 'error': 'Payout not found'}
    
    # Check if payout is approved
    if payout.status not in [InstallerPayout.PayoutStatus.APPROVED, InstallerPayout.PayoutStatus.PAID]:
        logger.warning(f"Payout {payout.short_id} is not approved, skipping Zoho sync")
        return {'success': False, 'error': 'Payout not approved'}
    
    # Check if already synced
    if payout.zoho_bill_id:
        logger.info(f"Payout {payout.short_id} already synced to Zoho (Bill ID: {payout.zoho_bill_id})")
        return {
            'success': True, 
            'message': 'Already synced',
            'bill_id': payout.zoho_bill_id
        }
    
    try:
        # Initialize Zoho client
        zoho_client = ZohoClient()
        
        # Prepare bill data
        # Note: This is a placeholder implementation
        # The actual Zoho Books API endpoint and format will need to be implemented
        # based on Zoho Books API documentation
        
        technician = payout.technician
        installations = payout.installations.all()
        
        bill_data = {
            'vendor_name': technician.user.get_full_name() or technician.user.username,
            'bill_number': payout.short_id,
            'date': payout.approved_at.strftime('%Y-%m-%d') if payout.approved_at else timezone.now().strftime('%Y-%m-%d'),
            'due_date': (payout.approved_at or timezone.now() + timezone.timedelta(days=30)).strftime('%Y-%m-%d'),
            'line_items': [],
            'notes': payout.calculation_method or f"Payout for {len(installations)} installation(s)",
        }
        
        # Add line items for each installation
        for installation in installations:
            bill_data['line_items'].append({
                'name': f"Installation - {installation.short_id}",
                'description': (
                    f"{installation.get_installation_type_display()} - "
                    f"{installation.customer.get_full_name() or installation.customer.contact.whatsapp_id}"
                ),
                'rate': float(payout.payout_amount / len(installations)),
                'quantity': 1,
            })
        
        # TODO: Implement actual Zoho Books API call
        # This would require adding a new method to ZohoClient for creating bills
        # For now, we'll mark as pending implementation
        
        logger.warning(
            f"Zoho Books API integration not yet fully implemented. "
            f"Would create bill for payout {payout.short_id} with amount ${payout.payout_amount}"
        )
        
        # Update payout with sync status
        payout.zoho_sync_status = 'pending_implementation'
        payout.zoho_sync_error = 'Zoho Books API integration pending implementation'
        payout.zoho_synced_at = timezone.now()
        payout.save()
        
        return {
            'success': True,
            'message': 'Zoho sync marked as pending implementation',
            'payout_id': str(payout.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to sync payout {payout.short_id} to Zoho: {e}")
        
        # Update payout with error
        payout.zoho_sync_status = 'error'
        payout.zoho_sync_error = str(e)
        payout.save()
        
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(queue='celery')
def send_payout_approval_email(payout_id):
    """
    Send email notification to technician when payout is approved.
    
    Args:
        payout_id: UUID of the approved InstallerPayout
        
    Returns:
        dict: Email send result
    """
    from .models import InstallerPayout
    
    try:
        payout = InstallerPayout.objects.select_related(
            'technician__user',
            'approved_by'
        ).prefetch_related('installations').get(id=payout_id)
    except InstallerPayout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
        return {'success': False, 'error': 'Payout not found'}
    
    # Get technician email
    technician_email = payout.technician.user.email
    if not technician_email:
        logger.warning(f"Technician {payout.technician} has no email address")
        return {'success': False, 'error': 'No email address'}
    
    try:
        # Prepare email context
        context = {
            'payout': payout,
            'technician': payout.technician,
            'technician_name': payout.technician.user.get_full_name() or payout.technician.user.username,
            'payout_amount': payout.payout_amount,
            'installation_count': payout.installations.count(),
            'approved_by': payout.approved_by.get_full_name() if payout.approved_by else 'Admin',
            'approved_at': payout.approved_at,
        }
        
        # Render email content
        subject = f"Payout Approved: {payout.short_id} - ${payout.payout_amount}"
        
        # Plain text message
        message = f"""
Dear {context['technician_name']},

Your payout request {payout.short_id} has been approved!

Payout Details:
- Amount: ${payout.payout_amount}
- Installations: {context['installation_count']}
- Approved by: {context['approved_by']}
- Approved on: {payout.approved_at.strftime('%B %d, %Y at %I:%M %p') if payout.approved_at else 'N/A'}

{payout.calculation_method if payout.calculation_method else ''}

The payment will be processed shortly. You will receive another notification once the payment is completed.

Best regards,
HANNA Installation Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[technician_email],
            fail_silently=False,
        )
        
        logger.info(f"Sent payout approval email to {technician_email} for payout {payout.short_id}")
        
        return {
            'success': True,
            'recipient': technician_email,
            'payout_id': str(payout.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to send payout approval email: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(queue='celery')
def send_payout_rejection_email(payout_id):
    """
    Send email notification to technician when payout is rejected.
    
    Args:
        payout_id: UUID of the rejected InstallerPayout
        
    Returns:
        dict: Email send result
    """
    from .models import InstallerPayout
    
    try:
        payout = InstallerPayout.objects.select_related(
            'technician__user'
        ).get(id=payout_id)
    except InstallerPayout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
        return {'success': False, 'error': 'Payout not found'}
    
    # Get technician email
    technician_email = payout.technician.user.email
    if not technician_email:
        logger.warning(f"Technician {payout.technician} has no email address")
        return {'success': False, 'error': 'No email address'}
    
    try:
        # Prepare email context
        context = {
            'payout': payout,
            'technician_name': payout.technician.user.get_full_name() or payout.technician.user.username,
            'rejection_reason': payout.rejection_reason or 'No reason provided',
        }
        
        # Render email content
        subject = f"Payout Rejected: {payout.short_id}"
        
        message = f"""
Dear {context['technician_name']},

Your payout request {payout.short_id} has been rejected.

Rejection Reason:
{context['rejection_reason']}

If you have questions about this decision, please contact the admin team.

Best regards,
HANNA Installation Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[technician_email],
            fail_silently=False,
        )
        
        logger.info(f"Sent payout rejection email to {technician_email} for payout {payout.short_id}")
        
        return {
            'success': True,
            'recipient': technician_email,
            'payout_id': str(payout.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to send payout rejection email: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(queue='celery')
def send_payout_payment_email(payout_id):
    """
    Send email notification to technician when payment is completed.
    
    Args:
        payout_id: UUID of the paid InstallerPayout
        
    Returns:
        dict: Email send result
    """
    from .models import InstallerPayout
    
    try:
        payout = InstallerPayout.objects.select_related(
            'technician__user'
        ).prefetch_related('installations').get(id=payout_id)
    except InstallerPayout.DoesNotExist:
        logger.error(f"Payout {payout_id} not found")
        return {'success': False, 'error': 'Payout not found'}
    
    # Get technician email
    technician_email = payout.technician.user.email
    if not technician_email:
        logger.warning(f"Technician {payout.technician} has no email address")
        return {'success': False, 'error': 'No email address'}
    
    try:
        # Prepare email context
        context = {
            'payout': payout,
            'technician_name': payout.technician.user.get_full_name() or payout.technician.user.username,
            'payout_amount': payout.payout_amount,
            'payment_reference': payout.payment_reference,
            'paid_at': payout.paid_at,
        }
        
        # Render email content
        subject = f"Payment Completed: {payout.short_id} - ${payout.payout_amount}"
        
        message = f"""
Dear {context['technician_name']},

Your payment for payout {payout.short_id} has been completed!

Payment Details:
- Amount: ${payout.payout_amount}
- Payment Reference: {payout.payment_reference}
- Payment Date: {payout.paid_at.strftime('%B %d, %Y at %I:%M %p') if payout.paid_at else 'N/A'}

The payment should reflect in your account shortly.

Thank you for your excellent work on the installations!

Best regards,
HANNA Installation Team
"""
        
        # Send email
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[technician_email],
            fail_silently=False,
        )
        
        logger.info(f"Sent payout payment email to {technician_email} for payout {payout.short_id}")
        
        return {
            'success': True,
            'recipient': technician_email,
            'payout_id': str(payout.id)
        }
        
    except Exception as e:
        logger.error(f"Failed to send payout payment email: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task(queue='celery')
def auto_create_payouts_for_completed_installations():
    """
    Periodic task to auto-create payouts for completed installations
    that don't have a payout yet.
    
    This should be scheduled to run daily or weekly.
    
    Returns:
        dict: Summary of created payouts
    """
    from .models import InstallationSystemRecord, InstallerPayout
    from .services import PayoutCalculationService
    
    logger.info("Running auto payout creation for completed installations")
    
    # Find completed installations without payouts
    completed_statuses = [
        InstallationSystemRecord.InstallationStatus.COMMISSIONED,
        InstallationSystemRecord.InstallationStatus.ACTIVE
    ]
    
    # Get installations that are completed and have no payouts
    installations_without_payouts = InstallationSystemRecord.objects.filter(
        installation_status__in=completed_statuses
    ).exclude(
        payouts__isnull=False
    ).prefetch_related('technicians').distinct()
    
    created_payouts = []
    errors = []
    
    for installation in installations_without_payouts:
        try:
            payouts = PayoutCalculationService.auto_create_payout_for_installation(installation)
            if payouts:
                created_payouts.extend(payouts)
                logger.info(
                    f"Created {len(payouts)} payout(s) for installation {installation.short_id}"
                )
        except Exception as e:
            logger.error(
                f"Failed to create payout for installation {installation.short_id}: {e}"
            )
            errors.append({
                'installation_id': str(installation.id),
                'error': str(e)
            })
    
    logger.info(
        f"Auto payout creation complete. Created: {len(created_payouts)}, Errors: {len(errors)}"
    )
    
    return {
        'success': True,
        'created_count': len(created_payouts),
        'error_count': len(errors),
        'created_payouts': [str(p.id) for p in created_payouts],
        'errors': errors
    }
