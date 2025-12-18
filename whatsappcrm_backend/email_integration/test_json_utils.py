"""
Tests for robust JSON parsing utilities.
"""
import json
from django.test import TestCase

from email_integration.json_utils import (
    extract_json_from_markdown,
    fix_json_syntax_errors,
    parse_json_robustly,
    validate_gemini_response_structure,
)


class ExtractJsonFromMarkdownTests(TestCase):
    """Tests for extracting JSON from markdown code blocks."""
    
    def test_extract_from_json_code_block(self):
        """Test extracting JSON from ```json code block."""
        text = '```json\n{"key": "value"}\n```'
        result = extract_json_from_markdown(text)
        self.assertEqual(result, '{"key": "value"}')
    
    def test_extract_from_json_code_block_with_extra_whitespace(self):
        """Test extracting JSON with extra whitespace in code block."""
        text = '```json\n  \n  {"key": "value"}  \n  \n```'
        result = extract_json_from_markdown(text)
        self.assertEqual(result, '{"key": "value"}')
    
    def test_extract_from_generic_code_block(self):
        """Test extracting JSON from generic ``` code block."""
        text = '```\n{"key": "value"}\n```'
        result = extract_json_from_markdown(text)
        self.assertEqual(result, '{"key": "value"}')
    
    def test_extract_json_object_without_markdown(self):
        """Test extracting plain JSON object without markdown."""
        text = 'Some text before {"key": "value"} some text after'
        result = extract_json_from_markdown(text)
        self.assertEqual(result, '{"key": "value"}')
    
    def test_extract_json_array(self):
        """Test extracting JSON array."""
        text = 'Some text [{"key": "value"}] more text'
        result = extract_json_from_markdown(text)
        self.assertEqual(result, '[{"key": "value"}]')
    
    def test_plain_json_without_wrapper(self):
        """Test handling plain JSON without any wrapper."""
        text = '{"key": "value"}'
        result = extract_json_from_markdown(text)
        self.assertEqual(result, '{"key": "value"}')
    
    def test_empty_text(self):
        """Test handling empty text."""
        result = extract_json_from_markdown('')
        self.assertIsNone(result)
    
    def test_none_text(self):
        """Test handling None text."""
        result = extract_json_from_markdown(None)
        self.assertIsNone(result)


class FixJsonSyntaxErrorsTests(TestCase):
    """Tests for fixing common JSON syntax errors."""
    
    def test_fix_trailing_comma_in_object(self):
        """Test fixing trailing comma in object."""
        json_str = '{"key": "value",}'
        result = fix_json_syntax_errors(json_str)
        self.assertEqual(result, '{"key": "value"}')
        # Verify it's valid JSON now
        json.loads(result)
    
    def test_fix_trailing_comma_in_array(self):
        """Test fixing trailing comma in array."""
        json_str = '[1, 2, 3,]'
        result = fix_json_syntax_errors(json_str)
        self.assertEqual(result, '[1, 2, 3]')
        json.loads(result)
    
    def test_fix_trailing_comma_in_nested_structure(self):
        """Test fixing trailing comma in nested structure (the original bug)."""
        json_str = '''{"items": [
            {"name": "item1", "value": 1},
            {"name": "item2", "value": 2}
        ]}'''
        # This is already valid, but let's test with invalid
        json_str_invalid = '''{"items": [
            {"name": "item1", "value": 1},
            {"name": "item2", "value": 2},
        ]}'''
        result = fix_json_syntax_errors(json_str_invalid)
        # Should be able to parse now
        parsed = json.loads(result)
        self.assertEqual(len(parsed['items']), 2)
    
    def test_fix_multiple_consecutive_commas(self):
        """Test fixing multiple consecutive commas."""
        json_str = '{"key1": "value1",, "key2": "value2"}'
        result = fix_json_syntax_errors(json_str)
        # Should reduce to single comma
        self.assertNotIn(',,', result)
    
    def test_real_world_example_from_issue(self):
        """Test the exact scenario from the GitHub issue."""
        # This is the problematic JSON from the issue
        json_str = '''{"line_items": [
      {
        "product_code": "OB-MP-GB-920001211",
        "description": "SOLAR BATTERY",
        "quantity": 1,
        "unit_price": 651.30,
        "total_amount": 749.00
      ,
      {
        "product_code": "OB-MP-GB-920001212",
        "description": "SOLAR INVERTER",
        "quantity": 1,
        "unit_price": 565.22,
        "total_amount": 650.00
      }
    ]}'''
        result = fix_json_syntax_errors(json_str)
        # Should be parseable now
        parsed = json.loads(result)
        self.assertEqual(len(parsed['line_items']), 2)
    
    def test_no_changes_needed(self):
        """Test that valid JSON is not modified."""
        json_str = '{"key": "value", "array": [1, 2, 3]}'
        result = fix_json_syntax_errors(json_str)
        # Should parse identically
        self.assertEqual(json.loads(json_str), json.loads(result))


class ParseJsonRobustlyTests(TestCase):
    """Tests for robust JSON parsing with fallback strategies."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        text = '{"key": "value"}'
        result = parse_json_robustly(text)
        self.assertEqual(result, {"key": "value"})
    
    def test_parse_json_from_markdown(self):
        """Test parsing JSON wrapped in markdown."""
        text = '```json\n{"key": "value"}\n```'
        result = parse_json_robustly(text)
        self.assertEqual(result, {"key": "value"})
    
    def test_parse_json_with_trailing_comma(self):
        """Test parsing JSON with trailing comma (auto-fix)."""
        text = '{"key": "value",}'
        result = parse_json_robustly(text)
        self.assertEqual(result, {"key": "value"})
    
    def test_parse_json_with_markdown_and_trailing_comma(self):
        """Test parsing markdown-wrapped JSON with syntax error."""
        text = '```json\n{"items": [{"id": 1,}]}\n```'
        result = parse_json_robustly(text)
        self.assertEqual(result, {"items": [{"id": 1}]})
    
    def test_parse_complex_gemini_response(self):
        """Test parsing a complex response similar to Gemini's output."""
        text = '''```json
{
  "document_type": "invoice",
  "data": {
    "invoice_number": "INV-001",
    "line_items": [
      {
        "product_code": "PROD-1",
        "quantity": 1,
        "unit_price": 100.00
      ,
      {
        "product_code": "PROD-2",
        "quantity": 2,
        "unit_price": 50.00
      }
    ]
  }
}
```'''
        result = parse_json_robustly(text)
        self.assertEqual(result['document_type'], 'invoice')
        self.assertEqual(len(result['data']['line_items']), 2)
    
    def test_parse_empty_text_raises_error(self):
        """Test that empty text raises appropriate error."""
        with self.assertRaises(json.JSONDecodeError):
            parse_json_robustly('')
    
    def test_parse_invalid_json_raises_error(self):
        """Test that completely invalid JSON raises error."""
        with self.assertRaises(json.JSONDecodeError):
            parse_json_robustly('This is not JSON at all')
    
    def test_parse_with_log_prefix(self):
        """Test that log prefix is used without errors."""
        text = '{"key": "value"}'
        result = parse_json_robustly(text, log_prefix="[TEST]")
        self.assertEqual(result, {"key": "value"})


class ValidateGeminiResponseStructureTests(TestCase):
    """Tests for validating Gemini response structure."""
    
    def test_valid_invoice_response(self):
        """Test validation of valid invoice response."""
        data = {
            "document_type": "invoice",
            "data": {
                "invoice_number": "INV-001",
                "line_items": []
            }
        }
        is_valid, error = validate_gemini_response_structure(data)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_valid_job_card_response(self):
        """Test validation of valid job card response."""
        data = {
            "document_type": "job_card",
            "data": {
                "job_card_number": "JC-001"
            }
        }
        is_valid, error = validate_gemini_response_structure(data)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")
    
    def test_missing_document_type(self):
        """Test validation fails when document_type is missing."""
        data = {
            "data": {"invoice_number": "INV-001"}
        }
        is_valid, error = validate_gemini_response_structure(data)
        self.assertFalse(is_valid)
        self.assertIn("document_type", error)
    
    def test_missing_data_field(self):
        """Test validation fails when data field is missing."""
        data = {
            "document_type": "invoice"
        }
        is_valid, error = validate_gemini_response_structure(data)
        self.assertFalse(is_valid)
        self.assertIn("data", error)
    
    def test_invalid_document_type(self):
        """Test validation fails with invalid document_type."""
        data = {
            "document_type": "unknown_type",
            "data": {}
        }
        is_valid, error = validate_gemini_response_structure(data)
        self.assertFalse(is_valid)
        self.assertIn("Invalid document_type", error)
    
    def test_data_not_object(self):
        """Test validation fails when data is not an object."""
        data = {
            "document_type": "invoice",
            "data": "not an object"
        }
        is_valid, error = validate_gemini_response_structure(data)
        self.assertFalse(is_valid)
        self.assertIn("must be an object", error)
    
    def test_not_dict(self):
        """Test validation fails when response is not a dict."""
        data = ["not", "a", "dict"]
        is_valid, error = validate_gemini_response_structure(data)
        self.assertFalse(is_valid)
        self.assertIn("not a JSON object", error)


class IntegrationTests(TestCase):
    """Integration tests combining parsing and validation."""
    
    def test_full_pipeline_with_valid_response(self):
        """Test the full pipeline with a valid Gemini-like response."""
        text = '''```json
{
  "document_type": "invoice",
  "data": {
    "invoice_number": "INV-123",
    "total_amount": 100.00
  }
}
```'''
        # Parse
        parsed = parse_json_robustly(text)
        # Validate
        is_valid, error = validate_gemini_response_structure(parsed)
        self.assertTrue(is_valid)
        self.assertEqual(parsed['document_type'], 'invoice')
    
    def test_full_pipeline_with_syntax_error(self):
        """Test the full pipeline with a response containing syntax errors."""
        text = '''```json
{
  "document_type": "invoice",
  "data": {
    "invoice_number": "INV-123",
    "line_items": [
      {"id": 1, "name": "Item 1"},
      {"id": 2, "name": "Item 2"},
    ],
  }
}
```'''
        # Parse (should auto-fix trailing commas)
        parsed = parse_json_robustly(text)
        # Validate
        is_valid, error = validate_gemini_response_structure(parsed)
        self.assertTrue(is_valid)
        self.assertEqual(len(parsed['data']['line_items']), 2)
    
    def test_full_pipeline_with_invalid_structure(self):
        """Test the full pipeline with structurally invalid response."""
        text = '''```json
{
  "wrong_type_field": "invoice",
  "data": {}
}
```'''
        # Parse (succeeds)
        parsed = parse_json_robustly(text)
        # Validate (fails)
        is_valid, error = validate_gemini_response_structure(parsed)
        self.assertFalse(is_valid)
        self.assertIn("document_type", error)
