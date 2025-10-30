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