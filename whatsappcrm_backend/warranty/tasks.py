from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import WarrantyClaim
import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="warranty.send_manufacturer_notification_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3}
)
def send_manufacturer_notification_task(self, claim_id: str, manufacturer_email: str):
    """
    Sends an email notification to the product manufacturer about a new warranty claim.
    """
    log_prefix = f"[Manufacturer Notify Task for Claim ID: {claim_id}]"
    logger.info(f"{log_prefix} Starting task to notify {manufacturer_email}.")

    try:
        claim = WarrantyClaim.objects.select_related(
            'warranty__product',
            'warranty__customer__contact'
        ).get(id=claim_id)

        product = claim.warranty.product
        customer = claim.warranty.customer

        subject = f"New Warranty Claim Filed for Product: {product.name} (SN: {claim.warranty.product_serial_number})"

        message = f"""
Dear Manufacturer,

This is an automated notification to inform you of a new warranty claim that has been filed for one of your products.

Claim Details:
- Claim ID: {claim.claim_id}
- Product Name: {product.name}
- Product SKU: {product.sku or 'N/A'}
- Serial Number: {claim.warranty.product_serial_number}
- Date of Claim: {claim.created_at.strftime('%Y-%m-%d')}

Fault Description Provided by Customer:
{claim.description_of_fault}

Please do not reply directly to this email. Our team will be in touch if further action is required.

Sincerely,
The Hanna Installations Team
"""
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[manufacturer_email],
            fail_silently=False,
        )
        logger.info(f"{log_prefix} Successfully sent notification email to {manufacturer_email}.")
        return f"Email sent to {manufacturer_email} for claim {claim_id}."

    except WarrantyClaim.DoesNotExist:
        logger.error(f"{log_prefix} WarrantyClaim with ID {claim_id} not found. Cannot send email.")
    except Exception as e:
        logger.error(f"{log_prefix} An unexpected error occurred: {e}", exc_info=True)
        raise self.retry(exc=e)


@shared_task(queue='celery')
def monitor_sla_compliance():
    """
    Periodic task to monitor SLA compliance and send alerts.
    Should be run every hour via Celery Beat.
    """
    from .models import SLAStatus
    from notifications.services import NotificationService
    from django.utils import timezone
    
    logger.info("Starting SLA compliance monitoring task")
    
    try:
        # Get all active SLA statuses (not yet completed)
        active_statuses = SLAStatus.objects.filter(
            resolution_completed_at__isnull=True
        )
        
        notifications_sent = 0
        
        for sla_status in active_statuses:
            # Update status to reflect current time
            sla_status.update_status()
            
            # Check if notification should be sent
            if sla_status.should_send_notification():
                try:
                    # Get the request object
                    request_object = sla_status.content_object
                    
                    # Prepare notification context
                    context = {
                        'request_type': sla_status.sla_threshold.get_request_type_display(),
                        'request_id': str(request_object.pk),
                        'response_status': sla_status.get_response_status_display(),
                        'resolution_status': sla_status.get_resolution_status_display(),
                        'response_deadline': sla_status.response_time_deadline,
                        'resolution_deadline': sla_status.resolution_time_deadline,
                    }
                    
                    # Determine recipients based on request type
                    recipients = []
                    
                    # Add customer if available
                    if hasattr(request_object, 'customer') and request_object.customer is not None:
                        if hasattr(request_object.customer, 'email') and request_object.customer.email:
                            recipients.append(request_object.customer.email)
                    
                    # Send notification to each recipient
                    for recipient_email in recipients:
                        NotificationService.send_notification(
                            recipient_email=recipient_email,
                            template_name='sla_alert',
                            context=context,
                            channel='email'
                        )
                    
                    # Update last notification time
                    sla_status.last_notification_sent = timezone.now()
                    sla_status.save()
                    
                    notifications_sent += 1
                    
                except Exception as e:
                    logger.error(f"Error sending SLA notification for {sla_status}: {str(e)}")
        
        logger.info(f"SLA monitoring completed. Sent {notifications_sent} notifications.")
        
    except Exception as e:
        logger.error(f"Error in SLA monitoring task: {str(e)}")
        raise


@shared_task(queue='celery')
def create_sla_status_for_request(request_type, request_id, request_model_name):
    """
    Create SLA status for a new request.
    
    Args:
        request_type: Type of request (matches SLAThreshold.RequestType)
        request_id: ID of the request object
        request_model_name: Name of the model (e.g., 'InstallationRequest', 'WarrantyClaim')
    """
    from django.apps import apps
    from .services import SLAService
    
    try:
        # Get the model class
        if request_model_name == 'WarrantyClaim':
            model_class = apps.get_model('warranty', 'WarrantyClaim')
        elif request_model_name == 'InstallationRequest':
            model_class = apps.get_model('customer_data', 'InstallationRequest')
        elif request_model_name == 'SiteAssessmentRequest':
            model_class = apps.get_model('customer_data', 'SiteAssessmentRequest')
        else:
            logger.error(f"Unknown request model: {request_model_name}")
            return
        
        # Get the request object
        request_object = model_class.objects.get(pk=request_id)
        
        # Get created_at timestamp, defaulting to now if not available
        created_at = getattr(request_object, 'created_at', None) or timezone.now()
        
        # Create SLA status
        sla_status = SLAService.create_sla_status(
            request_object=request_object,
            request_type=request_type,
            created_at=created_at
        )
        
        if sla_status:
            logger.info(f"Created SLA status for {request_model_name} {request_id}")
        else:
            logger.warning(f"No SLA threshold configured for request type: {request_type}")
            
    except Exception as e:
        logger.error(f"Error creating SLA status for {request_model_name} {request_id}: {str(e)}")
        raise