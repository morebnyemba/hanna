# paynow_wrapper.py
import logging
import hashlib # Still needed for IPN verification
from decimal import Decimal
from typing import Dict, Any, Optional

from paynow import Paynow # Import the official SDK

logger = logging.getLogger(__name__)

class PaynowSDK: # This class will wrap the official Paynow SDK
    """ 
    A wrapper around the official Paynow Python SDK for Express Checkout.
    """
    def __init__(self, integration_id: str, integration_key: str, result_url: str, return_url: str):
        if not integration_id or not integration_key:
            raise ValueError("Paynow Integration ID and Key must be provided.")
        
        # The official SDK's Paynow constructor takes resulturl and returnurl.
        # These are the default URLs for payments created by this instance.
        self.paynow_instance = Paynow(integration_id, integration_key, result_url, return_url)
        self.integration_id = integration_id # Keep for IPN verification
        self.integration_key = integration_key # Keep for IPN verification
        logger.info(f"PaynowSDK wrapper initialized for Integration ID: {integration_id}")

    def initiate_express_checkout(
        self,
        amount: Decimal,
        reference: str,
        phone_number: str,
        email: str,
        paynow_method_type: str,
        description: str = "Wallet Deposit"
    ) -> Dict[str, Any]:
        """
        Initiates an Express Checkout payment using the official Paynow SDK.
        """
        try:
            # Create a payment object. The SDK's create_payment uses the result_url/return_url
            # set in the Paynow constructor unless explicitly overridden here.
            payment = self.paynow_instance.create_payment(
                reference,
                email
            )
            
            # Add the item (description and amount)
            payment.add(description, float(amount)) # SDK expects float for amount
            
            logger.info(f"PaynowSDK: Initiating Express Checkout for ref {reference}, amount {amount}, phone {phone_number}.")
            
            # Send the mobile payment request
            response = self.paynow_instance.send_mobile(payment, phone_number, paynow_method_type)
            
            # Log full response details for debugging
            logger.info(f"PaynowSDK: Response success={response.success}")
            logger.info(f"PaynowSDK: Response __dict__: {response.__dict__}")
            logger.info(f"PaynowSDK: Available attributes: {dir(response)}")
            
            # Log specific attributes
            for attr in ['paynow_reference', 'poll_url', 'pollUrl', 'instructions', 
                        'redirect_url', 'redirectUrl', 'qr_code_url', 'qrCodeUrl',
                        'deeplink', 'payment_link', 'paymentLink', 'hash', 'error']:
                val = getattr(response, attr, None)
                if val is not None:
                    logger.info(f"PaynowSDK: response.{attr} = {val} (type: {type(val).__name__})")

            if response.success:
                # For Express Checkout, there's no redirect_url.
                # The SDK returns instructions and a poll_url.
                # Different payment methods return different data:
                # - EcoCash/Telecash: USSD push to phone (instructions)
                # - Omari: Requires OTP from customer's phone
                # - Innbucks: Returns QR code or deeplink
                
                # Try both snake_case and camelCase attribute names
                paynow_reference = getattr(response, 'paynow_reference', None) or getattr(response, 'paynowReference', None)
                poll_url = getattr(response, 'poll_url', None) or getattr(response, 'pollUrl', None)
                instructions = getattr(response, 'instructions', None)
                
                # Omari specific: Check for OTP requirement
                requires_otp = getattr(response, 'requires_otp', None) or getattr(response, 'requiresOtp', None)
                
                # Innbucks specific: Check for QR code or deeplink  
                qr_code_url = getattr(response, 'qr_code_url', None) or getattr(response, 'qrCodeUrl', None)
                deeplink = getattr(response, 'deeplink', None) or getattr(response, 'payment_link', None) or getattr(response, 'paymentLink', None)
                
                # Also check for redirect_url which some methods might use
                redirect_url = getattr(response, 'redirect_url', None) or getattr(response, 'redirectUrl', None)
                
                # Convert all values to JSON-serializable types
                def safe_str(val):
                    if val is None:
                        return None
                    if isinstance(val, (str, int, float, bool)):
                        return val
                    if isinstance(val, type):
                        return None
                    return str(val)
                
                result = {
                    "success": True,
                    "payment_method": paynow_method_type,
                    "paynow_reference": safe_str(paynow_reference),
                    "poll_url": safe_str(poll_url),
                    "instructions": safe_str(instructions),
                    "redirect_url": safe_str(redirect_url),
                }
                
                # Add method-specific fields
                if paynow_method_type == 'omari':
                    result['requires_otp'] = bool(requires_otp)
                    result['message'] = "Omari payment initiated. Please enter the OTP from your phone."
                elif paynow_method_type == 'innbucks':
                    # For Innbucks, the payment_link/redirect_url is the QR code link
                    result['qr_code_url'] = safe_str(qr_code_url) or safe_str(redirect_url)
                    result['deeplink'] = safe_str(deeplink) or safe_str(redirect_url)
                    result['message'] = "Innbucks payment initiated. Use the payment link to complete payment."
                else:  # ecocash, telecash
                    result['message'] = "Payment initiated successfully. Please check your phone for a prompt."
                
                logger.info(f"PaynowSDK: {paynow_method_type} Express Checkout initiated. Reference: {result['paynow_reference']}, Poll URL: {result['poll_url']}, Redirect: {result.get('redirect_url')}")
                return result
            else:
                error_message = getattr(response, 'error', 'Unknown error from Paynow SDK.')
                logger.error(f"PaynowSDK: API returned an error: {error_message}. Full response: {response.__dict__}")
                return {"success": False, "message": f"Paynow error: {str(error_message)}"} # Ensure it's a string

        except Exception as e:
            logger.error(f"PaynowSDK: Unexpected error during Express Checkout initiation: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Internal error processing payment: {str(e)}"}

    def verify_ipn_callback(self, ipn_data: Dict[str, str]) -> bool:
        """
        Verifies the integrity of an IPN callback from Paynow using the generated hash.
        The official SDK does not provide a direct IPN verification method,
        so we retain our manual hash verification logic.
        """
        hash_received = ipn_data.get('hash')
        
        status = ipn_data.get('status', '')
        reference = ipn_data.get('reference', '')
        paynow_reference = ipn_data.get('paynowreference', '')
        amount = ipn_data.get('amount', '')
        
        # The IPN hash calculation is specific and usually involves these fields + integration key.
        # This is based on common Paynow IPN documentation patterns.
        expected_hash_string = f"{status}{reference}{paynow_reference}{amount}{self.integration_key}"
        expected_hash = hashlib.md5(expected_hash_string.encode('utf-8')).hexdigest().upper()
        
        return hash_received == expected_hash

    def check_transaction_status(self, poll_url: str) -> Dict[str, Any]:
        """
        Checks the status of a transaction using the poll URL.
        """
        try:
            status_response = self.paynow_instance.check_transaction_status(poll_url)
            logger.debug(f"PaynowSDK: Status check response for {poll_url}: {status_response.__dict__}")
            
            return {
                "success": True,
                "status": status_response.status,
                "paid": status_response.paid,
                "message": status_response.status # Use the status as a message
            }
        except Exception as e:
            logger.error(f"PaynowSDK: Error checking transaction status for {poll_url}: {str(e)}", exc_info=True)
            return {"success": False, "message": f"Error checking status: {str(e)}"}
