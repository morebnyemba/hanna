# conversations/utils.py
import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def normalize_phone_number(phone_number: str, default_country_code: str = '263') -> str:
    """
    Normalizes a phone number to E.164 format for WhatsApp.
    
    Args:
        phone_number: The phone number to normalize (e.g., "077 235 4523", "+263772354523", "0772354523")
        default_country_code: The country code to use if not present (default: '263' for Zimbabwe)
    
    Returns:
        Normalized phone number in E.164 format without '+' (e.g., "263772354523")
        
    Examples:
        >>> normalize_phone_number("077 235 4523")
        '263772354523'
        >>> normalize_phone_number("+263772354523")
        '263772354523'
        >>> normalize_phone_number("0772354523")
        '263772354523'
    """
    if not phone_number:
        return ""
    
    # Remove all non-digit characters except '+'
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # Remove the '+' if present
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # If the number starts with '0', it's likely a local number
    # Remove the leading '0' and add the country code
    if cleaned.startswith('0'):
        cleaned = default_country_code + cleaned[1:]
    
    # If the number doesn't start with a country code, add the default
    # Most country codes are 1-3 digits. Zimbabwe is 263 (3 digits).
    # We'll check if it starts with the default country code
    elif not cleaned.startswith(default_country_code):
        # Only add country code if the number doesn't already have one
        # This is a simple heuristic: if the number is too short, add country code
        if len(cleaned) < 10:
            cleaned = default_country_code + cleaned
    
    # Validate the result
    if len(cleaned) < 10 or len(cleaned) > 15:
        logger.warning(f"Phone number '{phone_number}' normalized to '{cleaned}' may be invalid (length: {len(cleaned)})")
    
    return cleaned
