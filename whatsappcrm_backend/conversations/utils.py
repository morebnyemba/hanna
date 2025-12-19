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
        >>> normalize_phone_number("0775014661/0773046797")
        '263775014661'
    """
    if not phone_number:
        return ""
    
    # Handle multiple phone numbers separated by common delimiters (/, \, |, or, etc.)
    # Take only the first phone number
    if any(delimiter in phone_number for delimiter in ['/', '\\', '|', ' or ', ' OR ', ',']):
        # Split by multiple possible delimiters
        parts = re.split(r'[/\\|,]|\s+or\s+|\s+OR\s+', phone_number)
        phone_number = parts[0].strip()
        if len(parts) > 1:
            logger.info(f"Multiple phone numbers detected. Using first: '{phone_number}' (original: '{parts}')")
    
    # Remove all non-digit characters except '+'
    cleaned = re.sub(r'[^\d+]', '', phone_number)
    
    # Remove the '+' if present
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # If the number starts with '0', it's likely a local number
    # Remove the leading '0' and add the country code
    if cleaned.startswith('0'):
        cleaned = default_country_code + cleaned[1:]
    
    # If the number doesn't start with the default country code, check if it needs one
    elif not cleaned.startswith(default_country_code):
        # Common country codes (1-3 digits) - this is a heuristic check
        # Most country codes: 1 (US/Canada), 20-99 (various), 200-999 (various)
        # If number doesn't start with a likely country code and is short, add default
        likely_has_country_code = (
            cleaned.startswith('1') and len(cleaned) >= 11 or  # US/Canada format
            (len(cleaned) >= 11 and cleaned[0] != '0')  # Other international formats
        )
        
        if not likely_has_country_code:
            cleaned = default_country_code + cleaned
    
    # Validate the result
    if len(cleaned) < 10 or len(cleaned) > 15:
        logger.warning(f"Phone number '{phone_number}' normalized to '{cleaned}' may be invalid (length: {len(cleaned)})")
    
    return cleaned
