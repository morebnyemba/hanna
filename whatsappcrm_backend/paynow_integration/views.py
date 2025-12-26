# whatsappcrm_backend/paynow_integration/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import serializers
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.urls import reverse
import logging
import json
import uuid
from decimal import Decimal, InvalidOperation

from .models import PaynowConfig
from .serializers import PaynowConfigSerializer
from .services import PaynowService
from customer_data.models import Order, Payment, PaymentStatus
from django.conf import settings
from customer_data.receipts import generate_order_receipt_pdf

logger = logging.getLogger(__name__)

# URL path constant for IPN callback - used in initiate_whatsapp_payment and paynow_ipn_handler
PAYNOW_IPN_URL_PATH = '/api/paynow/ipn/'


class PaynowConfigViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing Paynow Configuration.
    There should only be one instance.
    """
    queryset = PaynowConfig.objects.all()
    serializer_class = PaynowConfigSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # Ensure we always work with the first (and ideally only) config object
        return PaynowConfig.objects.all().order_by('id')

    def list(self, request, *args, **kwargs):
        # Return the first object, or an empty response if none exists
        instance = self.get_queryset().first()
        if instance:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        return Response({})

    def perform_create(self, serializer):
        # Ensure only one config exists
        if PaynowConfig.objects.exists():
            raise serializers.ValidationError("A Paynow configuration already exists.")
        serializer.save()


@api_view(['POST'])
@permission_classes([permissions.AllowAny])  # Allow anonymous access for WhatsApp flow endpoint
def initiate_whatsapp_payment(request):
    """
    Endpoint to initiate a payment from a WhatsApp flow.
    
    Expected JSON body:
    {
        "order_number": "WA-12345",
        "phone_number": "263771234567",
        "email": "customer@example.com",
        "amount": "100.00",
        "payment_method": "ecocash",  # or "onemoney", "innbucks"
        "currency": "USD"
    }
    
    Returns:
    - 200 with payment details on success
    - 400 with error on failure
    """
    try:
        data = request.data
        
        order_number = data.get('order_number')
        phone_number = data.get('phone_number')
        payment_method = data.get('payment_method', 'ecocash')
        
        # Validate required fields
        if not all([order_number, phone_number]):
            return Response(
                {'success': False, 'message': 'Missing required fields: order_number, phone_number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get order from database (REQUIRED - source of truth for amount)
        try:
            order = Order.objects.select_related('customer').get(order_number=order_number)
            customer = order.customer
            # Use amount and currency from ORDER, not from client request
            amount = order.amount
            currency = order.currency
        except Order.DoesNotExist:
            return Response(
                {'success': False, 'message': f'Order {order_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get or use default email (required by Paynow for mobile transactions)
        email = data.get('email', '')
        if not email:
            # Use customer email if available, otherwise use company default
            if customer and customer.email:
                email = customer.email
            else:
                email = 'mnyemba@hanna.co.zw'  # Default company email for transactions
            logger.info(f"Using email for payment {payment_reference}: {email}")
        
        # Map payment method to Paynow method type
        paynow_method_map = {
            'ecocash': 'ecocash',
            'omari': 'omari',
            'innbucks': 'innbucks',
            'telecash': 'telecash'
        }
        paynow_method = paynow_method_map.get(payment_method.lower(), 'ecocash')
        
        # Create payment reference
        payment_reference = f"PAY-{order_number}-{uuid.uuid4().hex[:8].upper()}"
        
        # Initialize Paynow service using the constant
        paynow_service = PaynowService(ipn_callback_url=PAYNOW_IPN_URL_PATH)
        
        # Create Payment record first
        payment = Payment.objects.create(
            customer=customer,
            order=order,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            payment_method=paynow_method,
            provider_transaction_id=payment_reference
        )
        
        # Initiate Paynow payment
        result = paynow_service.initiate_express_checkout_payment(
            amount=amount,
            reference=payment_reference,
            phone_number=phone_number,
            email=email,
            paynow_method_type=paynow_method,
            description=f"Payment for Order {order_number}"
        )
        
        if result.get('success'):
            # Update payment with Paynow details
            payment.poll_url = result.get('poll_url')
            payment.provider_response = result
            payment.save(update_fields=['poll_url', 'provider_response'])
            
            # Update order payment status if order exists
            if order:
                order.payment_status = Order.PaymentStatus.PENDING
                order.save(update_fields=['payment_status'])
            
            logger.info(f"Payment initiated successfully: {payment_reference} via {paynow_method}")
            
            response_data = {
                'success': True,
                'message': result.get('message', 'Payment initiated successfully'),
                'payment_id': str(payment.id),
                'payment_reference': payment_reference,
                'payment_method': paynow_method,
                'poll_url': result.get('poll_url'),
                'paynow_reference': result.get('paynow_reference'),
                'instructions': result.get('instructions', f'Please check your {paynow_method} to complete the payment.')
            }
            
            # Add method-specific fields
            if paynow_method == 'omari' and result.get('requires_otp'):
                response_data['requires_otp'] = True
                response_data['otp_message'] = 'Please check your Omari phone for an OTP and enter it below.'
                if result.get('authorization_code'):
                    response_data['authorization_code'] = result.get('authorization_code')
                    response_data['authorization_expires'] = result.get('authorization_expires')
            elif paynow_method == 'innbucks':
                if result.get('authorization_code'):
                    response_data['authorization_code'] = result.get('authorization_code')
                    response_data['authorization_expires'] = result.get('authorization_expires')
                if result.get('deeplink'):
                    response_data['deeplink'] = result.get('deeplink')
            
            return Response(response_data)
        else:
            # Payment initiation failed
            payment.status = PaymentStatus.FAILED
            payment.provider_response = result
            payment.save(update_fields=['status', 'provider_response'])
            
            logger.error(f"Payment initiation failed: {result.get('message')}")
            
            return Response({
                'success': False,
                'message': result.get('message', 'Payment initiation failed'),
                'payment_id': str(payment.id)
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error initiating WhatsApp payment: {e}", exc_info=True)
        return Response({
            'success': False,
            'message': f'Server error: {str(e)[:200]}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def submit_omari_otp(request):
    """
    Submit Omari OTP to complete payment.
    Omari requires the customer to receive an OTP on their phone
    and submit it back to Paynow to authorize the transaction.
    """
    try:
        payment_reference = request.data.get('payment_reference')
        otp_code = request.data.get('otp_code')
        
        if not payment_reference or not otp_code:
            return Response({
                'success': False,
                'message': 'Payment reference and OTP code are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"Submitting Omari OTP for payment: {payment_reference}")
        
        # Get payment record
        try:
            payment = Payment.objects.get(provider_transaction_id=payment_reference)
        except Payment.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Payment not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Initialize Paynow service
        paynow_service = PaynowService(ipn_callback_url=PAYNOW_IPN_URL_PATH)
        
        # Submit OTP to Paynow (assuming the SDK has this method)
        # Note: The actual Paynow SDK might not have this method yet
        # In that case, we'd need to make a direct API call
        if hasattr(paynow_service.paynow_sdk, 'submit_otp'):
            result = paynow_service.paynow_sdk.submit_otp(
                poll_url=payment.poll_url,
                otp_code=otp_code
            )
            
            if result.get('success'):
                logger.info(f"Omari OTP submitted successfully for {payment_reference}")
                return Response({
                    'success': True,
                    'message': 'OTP submitted successfully. Please wait for payment confirmation.',
                    'poll_url': payment.poll_url
                })
            else:
                logger.error(f"Omari OTP submission failed: {result.get('message')}")
                return Response({
                    'success': False,
                    'message': result.get('message', 'OTP submission failed')
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            # SDK doesn't support OTP submission yet
            logger.warning(f"Paynow SDK doesn't support OTP submission. Payment: {payment_reference}")
            return Response({
                'success': False,
                'message': 'Omari OTP submission not yet implemented in SDK. Please complete payment via Omari app directly.'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
    except Exception as e:
        logger.error(f"Error submitting Omari OTP: {e}", exc_info=True)
        return Response({
            'success': False,
            'message': f'Server error: {str(e)[:200]}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def paynow_ipn_handler(request):
    """
    Instant Payment Notification (IPN) handler for Paynow callbacks.
    Paynow sends status updates to this endpoint when payment status changes.
    """
    try:
        # Paynow sends data as form-encoded
        ipn_data = request.POST.dict() if request.POST else request.data
        
        logger.info(f"Received Paynow IPN: {ipn_data}")
        
        # Extract relevant fields
        reference = ipn_data.get('reference', '')
        paynow_reference = ipn_data.get('paynowreference', '')
        amount = ipn_data.get('amount', '')
        status_val = ipn_data.get('status', '').lower()
        poll_url = ipn_data.get('pollurl', '')
        ipn_hash = ipn_data.get('hash', '')
        
        if not reference:
            logger.warning("IPN received without reference")
            return HttpResponse("Missing reference", status=400)
        
        # Verify hash using the constant
        paynow_service = PaynowService(ipn_callback_url=PAYNOW_IPN_URL_PATH)
        
        if not paynow_service.verify_ipn_hash(ipn_data):
            logger.error(f"IPN hash verification failed for reference: {reference}")
            return HttpResponse("Invalid hash", status=403)
        
        # Find payment by reference
        try:
            payment = Payment.objects.get(provider_transaction_id=reference)
        except Payment.DoesNotExist:
            logger.error(f"Payment not found for reference: {reference}")
            return HttpResponse("Payment not found", status=404)
        
        # Map Paynow status to our status
        status_map = {
            'paid': PaymentStatus.SUCCESSFUL,
            'awaiting delivery': PaymentStatus.AWAITING_DELIVERY,
            'delivered': PaymentStatus.DELIVERED,
            'cancelled': PaymentStatus.CANCELLED,
            'failed': PaymentStatus.FAILED,
            'refunded': PaymentStatus.CANCELLED,
            'disputed': PaymentStatus.PENDING,
            'sent': PaymentStatus.PENDING,
            'created': PaymentStatus.PENDING
        }
        
        new_status = status_map.get(status_val, PaymentStatus.PENDING)
        
        # Update payment
        payment.status = new_status
        payment.provider_response = ipn_data
        if poll_url:
            payment.poll_url = poll_url
        payment.save()
        
        logger.info(f"Payment {reference} updated to status: {new_status}")
        
        # Update order if payment was successful
        if new_status == PaymentStatus.SUCCESSFUL and payment.order:
            payment.order.payment_status = Order.PaymentStatus.PAID
            payment.order.save(update_fields=['payment_status'])
            logger.info(f"Order {payment.order.order_number} marked as PAID")
            
            # Send confirmation to customer via WhatsApp
            try:
                from meta_integration.utils import send_whatsapp_message
                from conversations.models import Contact
                
                if payment.customer and payment.customer.contact:
                    contact = payment.customer.contact
                    # 1) Send text confirmation
                    confirmation_msg = (
                        f"✅ *Payment Received!*\n\n"
                        f"Thank you! Your payment of ${payment.amount} {payment.currency} for "
                        f"order #{payment.order.order_number} has been confirmed.\n\n"
                        f"Reference: {paynow_reference}\n\n"
                        f"We will process your order shortly."
                    )
                    send_whatsapp_message(
                        to_phone_number=contact.whatsapp_id,
                        message_type='text',
                        data={'body': confirmation_msg}
                    )

                    # 2) Generate provisional receipt PDF and send document link
                    try:
                        abs_path, rel_url = generate_order_receipt_pdf(payment.order, payment)
                        backend_domain = getattr(settings, 'BACKEND_DOMAIN_FOR_CSP', None)
                        if backend_domain:
                            absolute_url = f"https://{backend_domain}{rel_url}"
                            caption = f"Provisional Receipt for Order #{payment.order.order_number}"
                            send_whatsapp_message(
                                to_phone_number=contact.whatsapp_id,
                                message_type='document',
                                data={
                                    'link': absolute_url,
                                    'caption': caption
                                }
                            )
                        else:
                            logger.error("BACKEND_DOMAIN_FOR_CSP not set; cannot form absolute receipt URL for WhatsApp document.")
                    except Exception as rec_e:
                        logger.error(f"Failed to generate/send receipt PDF: {rec_e}")
            except Exception as e:
                logger.error(f"Failed to send payment confirmation: {e}")
        
        return HttpResponse("OK", status=200)
        
    except Exception as e:
        logger.error(f"Error processing Paynow IPN: {e}", exc_info=True)
        return HttpResponse(f"Error: {str(e)}", status=500)