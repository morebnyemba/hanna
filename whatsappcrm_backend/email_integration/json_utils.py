"""
Utilities for robust JSON parsing from AI API responses.
Handles common issues like markdown wrappers, trailing commas, and malformed JSON.
"""
import json
import re
import logging

logger = logging.getLogger(__name__)


def extract_json_from_markdown(text: str) -> str | None:
    """
    Extracts JSON content from markdown code blocks.
    
    Tries multiple patterns:
    1. ```json ... ```
    2. ``` ... ``` (generic code block)
    3. Plain JSON object { ... }
    
    Args:
        text: Raw text that may contain JSON wrapped in markdown
        
    Returns:
        Extracted JSON string or None if no JSON found
    """
    if not text:
        return None
    
    text = text.strip()
    
    # Try to find JSON within markdown code blocks with 'json' language specifier
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
    if json_match:
        return json_match.group(1).strip()
    
    # Try to find JSON within generic markdown code blocks
    generic_code_match = re.search(r'```\s*([\s\S]*?)\s*```', text)
    if generic_code_match:
        potential_json = generic_code_match.group(1).strip()
        # Verify it looks like JSON (starts with { or [)
        if potential_json and potential_json[0] in ('{', '['):
            return potential_json
    
    # Try to find a JSON object without markdown wrapping
    # Look for outermost braces/brackets
    json_object_match = re.search(r'(\{[\s\S]*\})', text)
    if json_object_match:
        return json_object_match.group(1).strip()
    
    json_array_match = re.search(r'(\[[\s\S]*\])', text)
    if json_array_match:
        return json_array_match.group(1).strip()
    
    # If no patterns match, return the original text (might be plain JSON)
    return text


def fix_json_syntax_errors(json_str: str) -> str:
    """
    Attempts to fix common JSON syntax errors.
    
    Handles:
    - Trailing commas in objects and arrays (both before and after closing braces)
    - Missing closing braces before commas (Gemini sometimes forgets to close objects)
    - Standalone commas on their own lines
    - Missing quotes around property names
    - Extra commas
    
    Args:
        json_str: Potentially malformed JSON string
        
    Returns:
        Fixed JSON string
    """
    if not json_str:
        return json_str
    
    # Fix missing closing brace/bracket before comma on next line
    # Pattern: value (number, string, boolean, null) at end of line, then newline,
    # then whitespace and comma. This suggests a missing closing brace.
    # Example:  "key": value\n    ,\n should become "key": value\n    },\n
    # But we need to keep the comma as a separator, so replace the line with just comma
    # with a line that has closing brace and comma
    json_str = re.sub(
        r'(:\s*(?:\d+\.?\d*|"[^"]*"|true|false|null))\s*\n(\s*),\s*\n',
        r'\1\n\2},\n',
        json_str
    )
    
    # Fix trailing commas BEFORE closing braces/brackets ONLY
    # Pattern: comma followed by optional whitespace and then } or ]
    # We use a negative lookahead to ensure we don't remove commas before opening braces
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    
    # Fix trailing commas AFTER closing braces/brackets
    # Pattern: } or ] followed by whitespace and then comma, but NOT if followed by another opening brace
    # This handles cases like:  }\n    ,\n  (at end of array/object)
    # But NOT:  },\n    { (which is valid array separator)
    json_str = re.sub(r'([}\]])(\s*),(\s*[}\]])', r'\1\2\3', json_str)
    
    # Fix multiple consecutive commas
    json_str = re.sub(r',(\s*),+', r',\1', json_str)
    
    # Fix missing quotes around property names (JavaScript-style objects)
    # Pattern: word characters followed by colon (but not already quoted)
    # This is more conservative - only fix obvious cases
    json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)
    
    return json_str


def parse_json_robustly(text: str, log_prefix: str = "") -> dict:
    """
    Robustly parse JSON from text with multiple fallback strategies.
    
    Strategy:
    1. Extract JSON from markdown if present
    2. Try direct JSON parsing
    3. If that fails, fix common syntax errors and retry
    4. If still failing, try more aggressive fixes
    
    Args:
        text: Raw text containing JSON
        log_prefix: Prefix for log messages
        
    Returns:
        Parsed JSON as a dictionary
        
    Raises:
        json.JSONDecodeError: If all parsing strategies fail
    """
    if not text:
        raise json.JSONDecodeError("Empty response text", "", 0)
    
    original_text = text
    
    # Step 1: Extract JSON from markdown
    extracted_json = extract_json_from_markdown(text)
    if extracted_json:
        logger.debug(f"{log_prefix} Extracted JSON from markdown wrapper")
        text = extracted_json
    
    # Step 2: Try direct parsing
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        logger.debug(f"{log_prefix} Direct JSON parsing failed: {e}. Attempting to fix syntax errors.")
    
    # Step 3: Fix common syntax errors and retry
    try:
        fixed_json = fix_json_syntax_errors(text)
        result = json.loads(fixed_json)
        logger.info(f"{log_prefix} Successfully parsed JSON after fixing syntax errors")
        return result
    except json.JSONDecodeError as e:
        logger.debug(f"{log_prefix} JSON parsing still failed after basic fixes: {e}")
    
    # Step 4: Try more aggressive extraction - find the largest valid JSON object
    try:
        # Try to find and parse progressively smaller sections
        # Start from the beginning and find where valid JSON ends
        for i in range(len(text), 0, -1):
            substring = text[:i].rstrip()
            if substring and substring[-1] in ('}', ']'):
                try:
                    result = json.loads(substring)
                    logger.warning(
                        f"{log_prefix} Parsed partial JSON (truncated at position {i}/{len(text)}). "
                        "Full response may have been cut off."
                    )
                    return result
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.debug(f"{log_prefix} Aggressive parsing strategy failed: {e}")
    
    # All strategies failed - raise the original error with helpful context
    error_sample = original_text[:500] + "..." if len(original_text) > 500 else original_text
    raise json.JSONDecodeError(
        f"Failed to parse JSON after trying all strategies. Sample: {error_sample}",
        original_text,
        0
    )


def validate_gemini_response_structure(data: dict) -> tuple[bool, str]:
    """
    Validates that the parsed JSON has the expected structure for Gemini responses.
    
    Expected structure:
    {
        "document_type": "invoice" | "job_card" | "unknown",
        "data": { ... }
    }
    
    Args:
        data: Parsed JSON dictionary
        
    Returns:
        Tuple of (is_valid, error_message)
        If is_valid is True, error_message will be empty.
    """
    if not isinstance(data, dict):
        return False, f"Response is not a JSON object, got {type(data).__name__}"
    
    if "document_type" not in data:
        return False, "Missing required field 'document_type'"
    
    if "data" not in data:
        return False, "Missing required field 'data'"
    
    document_type = data.get("document_type")
    if document_type not in ("invoice", "job_card", "unknown"):
        return False, f"Invalid document_type '{document_type}'. Expected 'invoice', 'job_card', or 'unknown'"
    
    data_content = data.get("data")
    if not isinstance(data_content, dict):
        return False, f"Field 'data' must be an object, got {type(data_content).__name__}"
    
    return True, ""
