# Gemini JSON Parsing Robustness Fix

## Problem

The Gemini File API occasionally returns malformed JSON responses that fail to parse, causing attachment processing to fail. The specific error encountered was:

```
Failed to decode JSON from Gemini response. Error: Expecting property name enclosed in double quotes: line 26 column 7 (char 717)
```

The malformed JSON had a missing closing brace in an array element, like this:

```json
{
  "line_items": [
    {
      "product_code": "SKU-001",
      "total_amount": 749.00
    ,
    {
      "product_code": "SKU-002",
      "total_amount": 650.00
    }
  ]
}
```

Note the comma after `749.00` instead of a closing brace `}`.

## Solution

Implemented a robust JSON parsing system with multiple fallback strategies:

### 1. Multiple Extraction Strategies
- Extract JSON from markdown code blocks (```json ... ```)
- Find JSON objects in plain text
- Remove markdown markers and parse

### 2. Automatic JSON Repair
The `_repair_json()` function automatically fixes common syntax errors:
- **Missing closing braces in array elements**: Detects patterns like `value\n,\n{` and converts to `value\n},\n{`
- **Trailing commas**: Removes commas before closing braces/brackets
- **Missing closing brackets**: Counts and adds missing `]`
- **Missing closing braces**: Counts and adds missing `}`

### 3. Enhanced Error Handling
- Better error messages with context
- Preserves raw response for debugging
- Separate error handling for ValueError and JSONDecodeError

## Code Changes

### New Functions Added

1. **`_parse_gemini_response(raw_response: str, log_prefix: str) -> dict`**
   - Main parsing function with multiple fallback strategies
   - Handles markdown-wrapped JSON and plain JSON
   - Attempts automatic repair on parse failures

2. **`_repair_json(json_text: str, log_prefix: str) -> str | None`**
   - Repairs common JSON syntax errors
   - Returns repaired JSON or None if no repairs possible
   - Logs all repairs made for debugging

### Modified Functions

- **`process_attachment_with_gemini()`**: Updated to use `_parse_gemini_response()` instead of inline parsing logic

## Testing

Comprehensive tests added to `email_integration/tests.py`:

- `GeminiJSONParsingTests.test_parse_valid_json_in_markdown`
- `GeminiJSONParsingTests.test_parse_valid_json_without_markdown`
- `GeminiJSONParsingTests.test_parse_json_with_extra_text`
- `GeminiJSONParsingTests.test_repair_json_missing_closing_brace`
- `GeminiJSONParsingTests.test_repair_json_missing_multiple_braces`
- `GeminiJSONParsingTests.test_repair_json_trailing_comma`
- `GeminiJSONParsingTests.test_repair_json_missing_bracket`
- `GeminiJSONParsingTests.test_parse_empty_response`
- `GeminiJSONParsingTests.test_parse_response_with_no_json`
- `GeminiJSONParsingTests.test_parse_completely_malformed_json`
- `GeminiJSONParsingTests.test_parse_real_world_malformed_example`

## Verification

The fix has been verified to successfully parse the actual malformed JSON from the error log:

✓ Document type correctly identified as "invoice"
✓ Customer reference number extracted: "AV01/0036838"  
✓ All 8 line items parsed successfully
✓ Total amount parsed: 2569.00

## Impact

- **Improved reliability**: Attachment processing will no longer fail due to minor JSON syntax errors from Gemini
- **Better debugging**: Enhanced logging provides visibility into what repairs were made
- **Graceful degradation**: If repair fails, the system still logs the issue with full context for manual review
- **Minimal changes**: The fix is surgical and doesn't affect other parts of the codebase

## Future Considerations

While this fix handles the most common JSON syntax errors, completely malformed JSON that cannot be repaired will still fail. This is intentional - we want to maintain data integrity and not risk misinterpreting severely corrupted responses.

If Gemini consistently produces malformed JSON, consider:
1. Reporting the issue to Google
2. Adjusting the prompt to request better-formatted output
3. Using response schemas (if supported by the API version)
