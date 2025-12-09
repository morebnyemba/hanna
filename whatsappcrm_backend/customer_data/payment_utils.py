# whatsappcrm_backend/customer_data/payment_utils.py
"""
Utility functions and templates for payment processing.
"""
from django.conf import settings
from typing import Tuple, Optional


def parse_payment_button_id(button_id: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parse a payment button ID into its components.
    
    Expected formats:
    - pay_paynow_{order_number} -> ('pay', 'paynow', order_number)
    - pay_manual_{order_number} -> ('pay', 'manual', order_number)
    - paynow_{method}_{order_number} -> ('paynow', method, order_number)
    
    Args:
        button_id: The button ID to parse
    
    Returns:
        Tuple of (action, method_or_type, order_number) or (None, None, None) if invalid
    """
    if not button_id:
        return None, None, None
    
    parts = button_id.split('_', 2)  # Split into max 3 parts
    
    if len(parts) < 3:
        return None, None, None
    
    action = parts[0]  # 'pay' or 'paynow'
    method_or_type = parts[1]  # 'paynow', 'manual', 'ecocash', 'onemoney', 'innbucks'
    order_number = parts[2]
    
    return action, method_or_type, order_number


def get_bank_transfer_instructions(order_number: str, amount: str, currency: str = 'USD') -> str:
    """
    Get bank transfer payment instructions for an order.
    
    Args:
        order_number: The order number/reference
        amount: The payment amount
        currency: The currency code (default: USD)
    
    Returns:
        Formatted bank transfer instructions message
    
    Raises:
        ValueError: If required payment settings are not configured
    """
    # Get bank details from settings
    bank_name = getattr(settings, 'PAYMENT_BANK_NAME', None)
    account_name = getattr(settings, 'PAYMENT_ACCOUNT_NAME', None)
    account_number = getattr(settings, 'PAYMENT_ACCOUNT_NUMBER', None)
    branch_name = getattr(settings, 'PAYMENT_BRANCH_NAME', None)
    
    # Check if all required settings are configured
    missing_settings = []
    if not bank_name:
        missing_settings.append('PAYMENT_BANK_NAME')
    if not account_name:
        missing_settings.append('PAYMENT_ACCOUNT_NAME')
    if not account_number:
        missing_settings.append('PAYMENT_ACCOUNT_NUMBER')
    if not branch_name:
        missing_settings.append('PAYMENT_BRANCH_NAME')
    
    if missing_settings:
        # Provide fallback message that's user-friendly
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Payment settings not configured: {', '.join(missing_settings)}")
        
        return (
            f"✅ *Payment Method Confirmed*\n\n"
            f"You have selected: *Manual Payment*\n\n"
            f"Order: #{order_number}\n"
            f"Amount: ${amount} {currency}\n\n"
            f"Our team will contact you shortly with payment details and instructions.\n\n"
            f"Please keep your order number handy: *{order_number}*"
        )
    
    instructions_msg = (
        f"✅ *Payment Method Confirmed*\n\n"
        f"You have selected: *Manual Payment*\n\n"
        f"Order: #{order_number}\n"
        f"Amount: ${amount} {currency}\n\n"
        f"📋 *Bank Transfer Instructions:*\n\n"
        f"*Bank Details:*\n"
        f"Bank: {bank_name}\n"
        f"Account Name: {account_name}\n"
        f"Account Number: {account_number}\n"
        f"Branch: {branch_name}\n\n"
        f"Please use order number *{order_number}* as your reference.\n\n"
        f"After making the payment, please send us the proof of payment (screenshot or receipt).\n\n"
        f"Our team will confirm your payment and process your order."
    )
    
    return instructions_msg


def get_cash_payment_instructions(order_number: str, amount: str, currency: str = 'USD') -> str:
    """
    Get cash payment instructions for an order.
    
    Args:
        order_number: The order number/reference
        amount: The payment amount
        currency: The currency code (default: USD)
    
    Returns:
        Formatted cash payment instructions message
    """
    office_address = getattr(settings, 'OFFICE_ADDRESS', '[Configure OFFICE_ADDRESS in settings]')
    office_hours = getattr(settings, 'OFFICE_HOURS', 'Monday - Friday: 8:00 AM - 5:00 PM\nSaturday: 9:00 AM - 1:00 PM')
    
    instructions_msg = (
        f"✅ *Payment Method Confirmed*\n\n"
        f"You have selected: *Cash Payment*\n\n"
        f"Order: #{order_number}\n"
        f"Amount: ${amount} {currency}\n\n"
        f"📋 *Cash Payment Instructions:*\n\n"
        f"Please visit our office to complete your cash payment.\n\n"
        f"*Office Address:*\n"
        f"{office_address}\n\n"
        f"*Operating Hours:*\n"
        f"{office_hours}\n\n"
        f"Quote order number *{order_number}* when making payment."
    )
    
    return instructions_msg


def is_automated_payment_method(payment_method: str) -> bool:
    """
    Check if a payment method is automated (requires system integration).
    
    Args:
        payment_method: The payment method string (e.g., 'paynow_ecocash', 'manual_bank_transfer')
    
    Returns:
        True if automated, False if manual
    """
    return payment_method.startswith('paynow_')


def is_manual_payment_method(payment_method: str) -> bool:
    """
    Check if a payment method is manual (requires offline payment).
    
    Args:
        payment_method: The payment method string
    
    Returns:
        True if manual, False if automated
    """
    return payment_method.startswith('manual_')


def validate_phone_number(phone_number: str, country_code: str = None) -> str:
    """
    Validate and format phone number for payment processing.
    
    Args:
        phone_number: The phone number to validate
        country_code: Optional country code (e.g., '263' for Zimbabwe). 
                     If not provided, uses PAYMENT_COUNTRY_CODE from settings or defaults to '263'
    
    Returns:
        Formatted phone number
    
    Raises:
        ValueError: If phone number is invalid
    """
    # Get country code from settings if not provided
    if country_code is None:
        country_code = getattr(settings, 'PAYMENT_COUNTRY_CODE', '263')
    
    # Remove any whitespace
    phone = phone_number.strip()
    
    # Remove common separators
    phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    
    # Check if it's a valid format
    if not phone.startswith(country_code):
        # Try to add country code if it starts with 0
        if phone.startswith('0'):
            phone = country_code + phone[1:]
        else:
            raise ValueError(
                f"Invalid phone number format: {phone_number}. "
                f"Expected format: {country_code}XXXXXXXXX"
            )
    
    # Validate length (mobile numbers are typically 12 digits with country code for Zimbabwe)
    expected_length = getattr(settings, 'PAYMENT_PHONE_LENGTH', 12)
    if len(phone) != expected_length:
        raise ValueError(
            f"Invalid phone number length: {phone_number}. "
            f"Expected {expected_length} digits ({country_code}XXXXXXXXX)"
        )
    
    return phone
