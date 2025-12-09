# whatsappcrm_backend/customer_data/payment_utils.py
"""
Utility functions and templates for payment processing.
"""
from django.conf import settings


def get_bank_transfer_instructions(order_number: str, amount: str, currency: str = 'USD') -> str:
    """
    Get bank transfer payment instructions for an order.
    
    Args:
        order_number: The order number/reference
        amount: The payment amount
        currency: The currency code (default: USD)
    
    Returns:
        Formatted bank transfer instructions message
    """
    # Get bank details from settings or use defaults
    bank_name = getattr(settings, 'PAYMENT_BANK_NAME', '[Configure PAYMENT_BANK_NAME in settings]')
    account_name = getattr(settings, 'PAYMENT_ACCOUNT_NAME', '[Configure PAYMENT_ACCOUNT_NAME in settings]')
    account_number = getattr(settings, 'PAYMENT_ACCOUNT_NUMBER', '[Configure PAYMENT_ACCOUNT_NUMBER in settings]')
    branch_name = getattr(settings, 'PAYMENT_BRANCH_NAME', '[Configure PAYMENT_BRANCH_NAME in settings]')
    
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


def validate_phone_number(phone_number: str) -> str:
    """
    Validate and format phone number for payment processing.
    
    Args:
        phone_number: The phone number to validate
    
    Returns:
        Formatted phone number
    
    Raises:
        ValueError: If phone number is invalid
    """
    # Remove any whitespace
    phone = phone_number.strip()
    
    # Remove common separators
    phone = phone.replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
    
    # Check if it's a valid format (Zimbabwe numbers: 263...)
    if not phone.startswith('263'):
        # Try to add country code if it starts with 0
        if phone.startswith('0'):
            phone = '263' + phone[1:]
        else:
            raise ValueError(f"Invalid phone number format: {phone_number}. Expected format: 263771234567")
    
    # Validate length (Zimbabwe mobile numbers are 12 digits with country code)
    if len(phone) != 12:
        raise ValueError(f"Invalid phone number length: {phone_number}. Expected 12 digits (263XXXXXXXXX)")
    
    return phone
