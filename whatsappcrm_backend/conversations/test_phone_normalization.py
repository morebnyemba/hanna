# conversations/test_phone_normalization.py
from django.test import TestCase
from .utils import normalize_phone_number


class PhoneNumberNormalizationTestCase(TestCase):
    """Test cases for phone number normalization utility."""
    
    def test_normalize_zimbabwe_number_with_leading_zero(self):
        """Test normalizing Zimbabwe number with leading 0."""
        result = normalize_phone_number("0772354523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_zimbabwe_number_with_spaces(self):
        """Test normalizing Zimbabwe number with spaces."""
        result = normalize_phone_number("077 235 4523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_zimbabwe_number_with_dashes(self):
        """Test normalizing Zimbabwe number with dashes."""
        result = normalize_phone_number("077-235-4523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_zimbabwe_number_with_plus_prefix(self):
        """Test normalizing Zimbabwe number with + prefix."""
        result = normalize_phone_number("+263772354523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_zimbabwe_number_already_correct(self):
        """Test that already correct format is unchanged."""
        result = normalize_phone_number("263772354523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_zimbabwe_number_with_parentheses(self):
        """Test normalizing Zimbabwe number with parentheses."""
        result = normalize_phone_number("(077) 235-4523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_empty_string(self):
        """Test that empty string returns empty string."""
        result = normalize_phone_number("", default_country_code='263')
        self.assertEqual(result, "")
    
    def test_normalize_none(self):
        """Test that None returns empty string."""
        result = normalize_phone_number(None, default_country_code='263')
        self.assertEqual(result, "")
    
    def test_normalize_different_country_code(self):
        """Test with a different country code (e.g., South Africa +27)."""
        result = normalize_phone_number("0821234567", default_country_code='27')
        self.assertEqual(result, "27821234567")
    
    def test_normalize_international_format_without_plus(self):
        """Test international format without + prefix."""
        result = normalize_phone_number("263771234567", default_country_code='263')
        self.assertEqual(result, "263771234567")
    
    def test_normalize_with_country_code_in_number(self):
        """Test number that already has country code."""
        result = normalize_phone_number("263 77 123 4567", default_country_code='263')
        self.assertEqual(result, "263771234567")
    
    def test_warns_on_short_number(self):
        """Test that very short numbers still get processed but logged as warning."""
        result = normalize_phone_number("077", default_country_code='263')
        self.assertEqual(result, "26377")  # Still processes, but would be logged as warning
    
    def test_normalize_with_plus_and_spaces(self):
        """Test number with + and spaces."""
        result = normalize_phone_number("+263 77 235 4523", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_multiple_numbers_separated_by_slash(self):
        """Test multiple numbers separated by slash - should use first."""
        result = normalize_phone_number("0775014661/0773046797", default_country_code='263')
        self.assertEqual(result, "263775014661")
    
    def test_normalize_multiple_numbers_separated_by_comma(self):
        """Test multiple numbers separated by comma - should use first."""
        result = normalize_phone_number("0772354523, 0773456789", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_multiple_numbers_separated_by_pipe(self):
        """Test multiple numbers separated by pipe - should use first."""
        result = normalize_phone_number("0772354523|0773456789", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_multiple_numbers_separated_by_or(self):
        """Test multiple numbers separated by 'or' - should use first."""
        result = normalize_phone_number("0772354523 or 0773456789", default_country_code='263')
        self.assertEqual(result, "263772354523")
    
    def test_normalize_multiple_numbers_separated_by_hyphen(self):
        """Test multiple numbers separated by hyphen - should use first."""
        result = normalize_phone_number("0773854789-0772368614", default_country_code='263')
        self.assertEqual(result, "263773854789")

