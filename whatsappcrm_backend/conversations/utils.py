# conversations/utils.py
import re
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Delimiters that unambiguously separate several phone numbers packed into one
# field, e.g. "0775014661/0773046797" (case-insensitive for 'or').
PHONE_DELIMITER_PATTERN = re.compile(r'[/\\|,]|\s+or\s+', re.IGNORECASE)

# A '-' is ambiguous: it separates two numbers in "0773854789-0772368614", but
# groups digits inside ONE number in "077-235-4523". It used to be an
# unconditional delimiter, which truncated every hyphenated number to its first
# group -- "263-77-235-4523" normalised to "263". flows/tasks.py normalises the
# recipient before dispatch, so those replies were addressed to a nonsense number
# and silently never arrived.
#
# Both readings are resolved by length: a hyphen only separates numbers when
# every side is long enough to BE a number on its own. Digit groups are short, so
# "077-235-4523" falls through to the non-digit cleanup that strips the hyphens.
MIN_DIGITS_FOR_STANDALONE_NUMBER = 7


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
    
    # Handle multiple phone numbers packed into one field. Take only the first.
    if PHONE_DELIMITER_PATTERN.search(phone_number):
        parts = [p.strip() for p in PHONE_DELIMITER_PATTERN.split(phone_number) if p and p.strip()]
        if len(parts) > 1:
            logger.info(f"Multiple phone numbers detected ({len(parts)} total). Using first number.")
        if parts:
            phone_number = parts[0]

    # Hyphens: separators only if every side stands alone as a number (see
    # MIN_DIGITS_FOR_STANDALONE_NUMBER), otherwise they are digit grouping.
    if '-' in phone_number:
        hyphen_parts = [p.strip() for p in phone_number.split('-') if p.strip()]
        if len(hyphen_parts) > 1 and all(
            len(re.sub(r'\D', '', part)) >= MIN_DIGITS_FOR_STANDALONE_NUMBER
            for part in hyphen_parts
        ):
            logger.info(
                f"Multiple hyphen-separated phone numbers detected "
                f"({len(hyphen_parts)} total). Using first number."
            )
            phone_number = hyphen_parts[0]
    
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
