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
                # The actual data is in response.data dictionary, not as direct attributes
                # response.instructions, response.redirect_url etc are class attributes (type objects)
                data = getattr(response, 'data', {})
                
                # Extract common fields from response.data
                paynow_reference = data.get('paynowreference') or data.get('paynowReference')
                poll_url = response.poll_url or data.get('pollurl') or data.get('pollUrl')
                
                # Different payment methods return different data:
                # - EcoCash/Telecash: USSD push to phone (authorization sent via USSD)
                # - Omari: Returns authorization code, customer receives OTP via SMS to authorize
                # - Innbucks: Returns authorization code that customer enters in Innbucks wallet
                
                # Common fields across methods that use authorization codes
                authorization_code = data.get('authorizationcode') or data.get('authorizationCode')
                authorization_expires = data.get('authorizationexpires') or data.get('authorizationExpires')
                
                # Build instructions based on payment method
                if paynow_method_type == 'omari' and authorization_code:
                    instructions = f"Authorization code: {authorization_code}. Check your phone for an OTP to complete payment. Code expires: {authorization_expires}"
                elif paynow_method_type == 'innbucks' and authorization_code:
                    instructions = f"Use authorization code: {authorization_code} to complete payment in your Innbucks wallet. Code expires: {authorization_expires}"
                    # Generate Innbucks deeplink (if applicable)
                    deeplink = f"innbucks://pay?code={authorization_code}&reference={paynow_reference}"
                else:
                    instructions = None
                    deeplink = None
                
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
                }
                
                # Add method-specific fields
                if paynow_method_type == 'omari':
                    # Omari always requires OTP - customer receives SMS with OTP after initiating payment
                    result['requires_otp'] = True
                    result['authorization_code'] = safe_str(authorization_code)
                    result['authorization_expires'] = safe_str(authorization_expires)
                    result['message'] = f"Omari payment initiated. Authorization: {authorization_code}. Please enter the OTP sent to your phone."
                elif paynow_method_type == 'innbucks':
                    result['authorization_code'] = safe_str(authorization_code)
                    result['authorization_expires'] = safe_str(authorization_expires)
                    result['deeplink'] = safe_str(deeplink) if deeplink else None
                    result['message'] = f"Innbucks payment initiated. Authorization code: {authorization_code}"
                else:  # ecocash, telecash
                    result['message'] = "Payment initiated successfully. Please check your phone for a prompt."
                
                logger.info(f"PaynowSDK: {paynow_method_type} Express Checkout initiated. Reference: {result['paynow_reference']}, Poll URL: {result['poll_url']}, Auth Code: {result.get('authorization_code')}")
                return result
            else:
                # Normalize error message to avoid rendering Python types like <class 'str'> to the UI
                raw_error = getattr(response, 'error', None)
                if isinstance(raw_error, type):
                    raw_error = None

                data_error = None
                data_payload = getattr(response, 'data', None)
                if isinstance(data_payload, dict):
                    data_error = data_payload.get('error') or data_payload.get('message')

                error_message = raw_error or data_error or 'Unknown error from Paynow SDK.'
                logger.error(f"PaynowSDK: API returned an error: {error_message}. Full response: {response.__dict__}")
                return {"success": False, "message": f"Paynow error: {error_message}"}

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
