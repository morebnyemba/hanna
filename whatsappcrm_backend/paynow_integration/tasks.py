# paynow_integration/tasks.py
"""
Celery fallback for confirming Paynow payments when the IPN callback never
arrives (webhooks are inherently unreliable - network blips, Paynow
misconfiguration, a firewall dropping the callback, etc). This polls
Paynow's poll_url directly for the transaction status and applies the same
idempotent update as the IPN handler in views.py.
"""
import logging
import random
import uuid
from decimal import Decimal

from celery import shared_task
from django.db import transaction

from .services import PaynowService
from customer_data.models import Payment, PaymentStatus, Order

logger = logging.getLogger(__name__)

# Must match paynow_integration/views.py PAYNOW_IPN_URL_PATH.
PAYNOW_IPN_URL_PATH = '/crm-api/paynow/ipn/'


@shared_task(name="paynow_integration.initiate_paynow_payment_task", bind=True, max_retries=2, default_retry_delay=5)
def initiate_paynow_payment_task(self, order_number: str, method: str, contact_whatsapp_id: str):
    """
    Initiates a Paynow Express Checkout payment for an order and messages the
    customer with the outcome.

    This used to run inline inside the WhatsApp webhook view (inside its
    @transaction.atomic block). The `paynow` SDK's underlying requests.post()
    calls (paynow/model.py) carry no timeout, so a slow or unresponsive Paynow
    endpoint could hang that HTTP request indefinitely -- wedging the ASGI
    connection (and the open DB transaction/row locks it held) until the
    process was restarted, during which the webhook stopped responding for
    every contact, not just the one paying. Running it as a Celery task keeps
    an unbounded third-party call off the request/response path entirely.
    """
    from customer_data.payment_utils import validate_phone_number
    from meta_integration.utils import send_whatsapp_message

    log_prefix = f"[Paynow Initiate - Order: {order_number}]"

    try:
        order = Order.objects.select_related('customer').get(order_number=order_number)
    except Order.DoesNotExist:
        logger.error(f"{log_prefix} Order not found.")
        return

    try:
        validated_phone = validate_phone_number(contact_whatsapp_id)
    except ValueError as e:
        logger.error(f"{log_prefix} Phone number validation failed: {e}")
        send_whatsapp_message(
            to_phone_number=contact_whatsapp_id,
            message_type='text',
            data={'body': (
                f"❌ Invalid phone number format.\n\n"
                f"Please contact our support team to complete your payment.\n"
                f"Order: #{order.order_number}"
            )}
        )
        return

    customer_email = ''
    if order.customer:
        customer_email = (order.customer.email or '').strip()
    if not customer_email:
        customer_email = 'mnyemba@hanna.co.zw'

    payment_reference = f"PAY-{order.order_number}-{uuid.uuid4().hex[:8].upper()}"
    paynow_service = PaynowService(ipn_callback_url=PAYNOW_IPN_URL_PATH)

    payment = Payment.objects.create(
        customer=order.customer,
        order=order,
        amount=order.amount,
        currency=order.currency,
        status=PaymentStatus.PENDING,
        payment_method=method,
        provider_transaction_id=payment_reference
    )

    try:
        result = paynow_service.initiate_express_checkout_payment(
            amount=Decimal(str(order.amount)),
            reference=payment_reference,
            phone_number=validated_phone,
            email=customer_email,
            paynow_method_type=method,
            description=f"Payment for Order {order.order_number}"
        )
    except Exception as e:
        # Without this, the Payment row this task just created is orphaned at
        # PENDING with no poll_url forever: the IPN can never arrive for a
        # checkout that was never actually initiated, and the poll fallback
        # below is never scheduled since it depends on a successful `result`.
        logger.error(f"{log_prefix} Error initiating Paynow payment: {e}", exc_info=True)
        payment.status = PaymentStatus.FAILED
        payment.provider_response = {'error': str(e), 'error_type': type(e).__name__}
        payment.save(update_fields=['status', 'provider_response'])
        send_whatsapp_message(
            to_phone_number=contact_whatsapp_id,
            message_type='text',
            data={'body': (
                f"❌ An error occurred while processing your payment.\n\n"
                f"Please contact our support team with order number: {order.order_number}"
            )}
        )
        return

    if result.get('success'):
        payment.poll_url = result.get('poll_url')
        payment.provider_response = result
        payment.save(update_fields=['poll_url', 'provider_response'])

        # Fallback in case the Paynow IPN callback never arrives.
        if payment.poll_url:
            poll_paynow_transaction_status.apply_async(args=[str(payment.id)], countdown=90)

        send_whatsapp_message(
            to_phone_number=contact_whatsapp_id,
            message_type='text',
            data={'body': (
                f"💳 *Payment Request Sent*\n\n"
                f"Please approve the payment on your phone.\n\n"
                f"Reference: {result.get('paynow_reference', 'N/A')}\n\n"
                f"You will receive a confirmation once payment is complete."
            )}
        )
        logger.info(f"{log_prefix} Paynow payment initiated. PaynowRef: {result.get('paynow_reference')}.")
    else:
        payment.status = PaymentStatus.FAILED
        payment.provider_response = result
        payment.save(update_fields=['status', 'provider_response'])

        send_whatsapp_message(
            to_phone_number=contact_whatsapp_id,
            message_type='text',
            data={'body': (
                f"❌ Payment initiation failed.\n\n"
                f"Reason: {result.get('message', 'Unknown error')}\n\n"
                f"Please try again or contact our support team."
            )}
        )
        logger.error(f"{log_prefix} Paynow payment failed: {result.get('message')}")


@shared_task(name="paynow_integration.poll_paynow_transaction_status", bind=True, max_retries=8, default_retry_delay=60)
def poll_paynow_transaction_status(self, payment_id: str):
    """
    Polls Paynow for the current status of a payment and updates the Payment/
    Order records accordingly. Intended to be scheduled a short delay after
    payment initiation as a safety net for missed IPNs - it's idempotent with
    the IPN handler (both check `status` before applying side effects), so it's
    safe for both to eventually observe the same "paid" transaction.
    """
    log_prefix = f"[Paynow Poll - Payment: {payment_id}]"

    try:
        with transaction.atomic():
            try:
                payment = Payment.objects.select_for_update().get(id=payment_id)
            except Payment.DoesNotExist:
                logger.warning(f"{log_prefix} Payment not found. Stopping poll.")
                return

            if payment.status != PaymentStatus.PENDING:
                logger.info(f"{log_prefix} Payment already in terminal/non-pending state '{payment.status}'. Stopping poll.")
                return

            if not payment.poll_url:
                logger.warning(f"{log_prefix} No poll_url on payment; cannot poll. Stopping.")
                return

            paynow_service = PaynowService(ipn_callback_url=PAYNOW_IPN_URL_PATH)
            status_response = paynow_service.check_transaction_status(payment.poll_url)

            if not status_response.get('success'):
                error_msg = status_response.get('message', 'Unknown error')
                logger.warning(f"{log_prefix} Failed to check status: {error_msg}. Will retry.")
                raise self.retry(exc=Exception(error_msg))

            paynow_status = (status_response.get('status') or '').lower()

            if paynow_status == 'paid':
                payment.status = PaymentStatus.SUCCESSFUL
                payment.provider_response = {**(payment.provider_response or {}), 'poll_status': status_response}
                payment.save(update_fields=['status', 'provider_response', 'updated_at'])

                if payment.order:
                    payment.order.payment_status = Order.PaymentStatus.PAID
                    payment.order.save(update_fields=['payment_status'])
                    logger.info(f"{log_prefix} Order {payment.order.order_number} marked as PAID via poll fallback.")
            elif paynow_status in ('cancelled', 'failed', 'disputed'):
                payment.status = PaymentStatus.FAILED
                payment.provider_response = {**(payment.provider_response or {}), 'poll_status': status_response}
                payment.save(update_fields=['status', 'provider_response', 'updated_at'])
                logger.info(f"{log_prefix} Payment marked FAILED (Paynow status: '{paynow_status}').")
            else:
                # Still pending - back off and retry rather than hammering Paynow.
                retry_delay = 30 * (2 ** self.request.retries) + random.randint(0, 10)
                logger.info(f"{log_prefix} Still '{paynow_status}'. Retrying in {retry_delay}s.")
                raise self.retry(countdown=retry_delay)

        # Send the same WhatsApp confirmation as the IPN handler, but only once
        # (guarded by the PENDING check above - this task only reaches here on
        # the transition into a terminal state).
        if paynow_status == 'paid' and payment.order and payment.customer and payment.customer.contact:
            _send_payment_confirmation(payment)

    except Payment.DoesNotExist:
        logger.warning(f"{log_prefix} Payment not found on retry. Stopping.")
    except self.MaxRetriesExceededError:
        logger.warning(f"{log_prefix} Max retries exceeded without a final status. Leaving payment PENDING for IPN/manual follow-up.")


def _send_payment_confirmation(payment: Payment):
    """Sends the WhatsApp payment-received message + provisional receipt PDF.
    Mirrors the notification logic in paynow_integration/views.py's IPN handler."""
    from django.conf import settings
    from meta_integration.utils import send_whatsapp_message
    from customer_data.receipts import generate_order_receipt_pdf

    try:
        contact = payment.customer.contact
        confirmation_msg = (
            f"✅ *Payment Received!*\n\n"
            f"Thank you! Your payment of ${payment.amount} {payment.currency} for "
            f"order #{payment.order.order_number} has been confirmed.\n\n"
            f"We will process your order shortly."
        )
        send_whatsapp_message(
            to_phone_number=contact.whatsapp_id,
            message_type='text',
            data={'body': confirmation_msg}
        )

        try:
            abs_path, rel_url = generate_order_receipt_pdf(payment.order, payment)
            backend_domain = getattr(settings, 'BACKEND_DOMAIN_FOR_CSP', None)
            if backend_domain:
                absolute_url = f"https://{backend_domain}{rel_url}"
                send_whatsapp_message(
                    to_phone_number=contact.whatsapp_id,
                    message_type='document',
                    data={
                        'link': absolute_url,
                        'caption': f"Provisional Receipt for Order #{payment.order.order_number}"
                    }
                )
        except Exception as rec_e:
            logger.error(f"Failed to generate/send receipt PDF for payment {payment.id}: {rec_e}")
    except Exception as e:
        logger.error(f"Failed to send payment confirmation for payment {payment.id}: {e}")
