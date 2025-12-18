from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json

from .models import EmailAttachment
from .tasks import _create_order_from_invoice_data, _parse_gemini_json_response
from customer_data.models import CustomerProfile, Order, OrderItem, Contact
from products_and_services.models import Product

class CreateOrderFromInvoiceDataTests(TestCase):

    def setUp(self):
        """Set up common objects for tests."""
        # Create a dummy file and an EmailAttachment instance
        dummy_file = SimpleUploadedFile("invoice.pdf", b"file_content", content_type="application/pdf")
        self.attachment = EmailAttachment.objects.create(
            file=dummy_file,
            filename="invoice.pdf",
            sender="testsender@example.com"
        )

        # A standard set of extracted data for a new customer and order
        self.invoice_data = {
            "invoice_number": "INV-123",
            "invoice_date": "2023-10-26",
            "total_amount": 150.00,
            "recipient": {
                "name": "John Doe",
                "phone": "+15551234567",
                "address": "123 Main St"
            },
            "line_items": [
                {
                    "product_code": "SKU-001",
                    "description": "Solar Panel 300W",
                    "quantity": 1,
                    "unit_price": 100.00,
                    "total_amount": 100.00
                },
                {
                    "product_code": "SKU-002",
                    "description": "Inverter 5kW",
                    "quantity": 1,
                    "unit_price": 50.00,
                    "total_amount": 50.00
                }
            ]
        }

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_create_order_for_new_customer(self, mock_queue_notifications):
        """Test creating a new order, customer, products, and items from scratch."""
        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # 1. Verify Contact and CustomerProfile were created
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)
        customer = CustomerProfile.objects.first()
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.contact.whatsapp_id, "15551234567")

        # 2. Verify Order was created
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.order_number, "INV-123")
        self.assertEqual(order.customer, customer)
        self.assertEqual(order.amount, 150.00)

        # 3. Verify Products and OrderItems were created
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(OrderItem.objects.count(), 2)
        self.assertEqual(order.items.count(), 2)
        self.assertTrue(Product.objects.filter(sku="SKU-001").exists())
        
        # 4. Verify products from email import are created as inactive
        for product in Product.objects.all():
            self.assertFalse(product.is_active, "Products created from email import should be inactive")

        # 5. Verify notification was queued
        mock_queue_notifications.assert_called_once()

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_update_existing_order(self, mock_queue_notifications):
        """Test that an existing order is updated and its items are replaced."""
        # Pre-create an order with the same invoice number
        existing_order = Order.objects.create(order_number="INV-123", amount=99.99)
        product = Product.objects.create(name="Old Product", price=99.99)
        OrderItem.objects.create(order=existing_order, product=product, quantity=1, unit_price=99.99)

        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)

        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # Verify order was updated, not created
        self.assertEqual(Order.objects.count(), 1)
        updated_order = Order.objects.get(order_number="INV-123")
        self.assertEqual(updated_order.amount, 150.00)

        # Verify old items were deleted and new ones were created
        self.assertEqual(updated_order.items.count(), 2)
        self.assertFalse(updated_order.items.filter(product__name="Old Product").exists())
        self.assertTrue(updated_order.items.filter(product__sku="SKU-001").exists())
        mock_queue_notifications.assert_called_once()

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_create_order_for_existing_customer(self, mock_queue_notifications):
        """Test that a new order is created for an existing customer without creating a new profile."""
        contact = Contact.objects.create(whatsapp_id="15551234567", name="John Doe")
        CustomerProfile.objects.create(contact=contact, first_name="John", last_name="Doe")

        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)

        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # No new contact or profile should be created
        self.assertEqual(Contact.objects.count(), 1)
        self.assertEqual(CustomerProfile.objects.count(), 1)

        # A new order should be created and linked to the existing customer
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(Order.objects.first().customer.contact.whatsapp_id, "15551234567")

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_use_existing_products(self, mock_queue_notifications):
        """Test that existing products are reused instead of creating duplicates."""
        Product.objects.create(sku="SKU-001", name="Pre-existing Panel", price=99.00)
        self.assertEqual(Product.objects.count(), 1)

        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        # Only one new product (SKU-002) should have been created
        self.assertEqual(Product.objects.count(), 2)
        order_item = OrderItem.objects.get(product__sku="SKU-001")
        # The name should not have been updated by get_or_create defaults
        self.assertEqual(order_item.product.name, "Pre-existing Panel")

    def test_no_invoice_number(self):
        """Test that the function exits gracefully if no invoice_number is present."""
        self.invoice_data.pop('invoice_number')
        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Contact.objects.count(), 0)

    @patch('email_integration.tasks.queue_notifications_to_users')
    def test_no_customer_phone(self, mock_queue_notifications):
        """Test that an order is created without a customer if the phone is missing."""
        self.invoice_data['recipient'].pop('phone')
        _create_order_from_invoice_data(self.attachment, self.invoice_data, "[Test]")

        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertIsNone(order.customer)

        # Notification should not be sent if there's no customer profile
        mock_queue_notifications.assert_not_called()


class AdminActionsTests(TestCase):
    """Test cases for admin actions in email_integration app."""

    def setUp(self):
        """Set up common objects for tests."""
        from django.contrib.auth import get_user_model
        from django.test import RequestFactory
        import uuid
        
        User = get_user_model()
        self.factory = RequestFactory()
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        # Create test attachments with unique filenames
        unique_id = str(uuid.uuid4())[:8]
        dummy_file = SimpleUploadedFile(
            f"test_{unique_id}_1.pdf", 
            b"file_content", 
            content_type="application/pdf"
        )
        self.attachment1 = EmailAttachment.objects.create(
            file=dummy_file,
            filename=f"test_{unique_id}_1.pdf",
            sender="test1@example.com",
            processed=True
        )
        
        dummy_file2 = SimpleUploadedFile(
            f"test_{unique_id}_2.pdf", 
            b"file_content2", 
            content_type="application/pdf"
        )
        self.attachment2 = EmailAttachment.objects.create(
            file=dummy_file2,
            filename=f"test_{unique_id}_2.pdf",
            sender="test2@example.com",
            processed=False
        )

    @patch('email_integration.admin.process_attachment_with_gemini')
    def test_retrigger_gemini_processing(self, mock_task):
        """Test the retrigger_gemini_processing admin action."""
        from email_integration.admin import retrigger_gemini_processing, EmailAttachmentAdmin
        
        # Mock the delay method
        mock_task.delay = MagicMock()
        
        # Create request
        request = self.factory.post('/admin/email_integration/emailattachment/')
        request.user = self.user
        
        # Create queryset
        queryset = EmailAttachment.objects.filter(id=self.attachment1.id)
        
        # Create mock admin instance
        modeladmin = EmailAttachmentAdmin(EmailAttachment, None)
        
        # Call the admin action
        retrigger_gemini_processing(modeladmin, request, queryset)
        
        # Verify the attachment was marked as unprocessed
        self.attachment1.refresh_from_db()
        self.assertFalse(self.attachment1.processed)
        
        # Verify the task was queued
        mock_task.delay.assert_called_once_with(self.attachment1.id)

    def test_mark_as_unprocessed(self):
        """Test the mark_as_unprocessed admin action."""
        from email_integration.admin import mark_as_unprocessed, EmailAttachmentAdmin
        
        # Create request
        request = self.factory.post('/admin/email_integration/emailattachment/')
        request.user = self.user
        
        # Create queryset with a processed attachment
        queryset = EmailAttachment.objects.filter(id=self.attachment1.id)
        
        # Verify it's currently processed
        self.assertTrue(self.attachment1.processed)
        
        # Create mock admin instance
        modeladmin = EmailAttachmentAdmin(EmailAttachment, None)
        
        # Call the admin action
        mark_as_unprocessed(modeladmin, request, queryset)
        
        # Verify the attachment was marked as unprocessed
        self.attachment1.refresh_from_db()
        self.assertFalse(self.attachment1.processed)

    def test_mark_as_processed(self):
        """Test the mark_as_processed admin action."""
        from email_integration.admin import mark_as_processed, EmailAttachmentAdmin
        
        # Create request
        request = self.factory.post('/admin/email_integration/emailattachment/')
        request.user = self.user
        
        # Create queryset with an unprocessed attachment
        queryset = EmailAttachment.objects.filter(id=self.attachment2.id)
        
        # Verify it's currently unprocessed
        self.assertFalse(self.attachment2.processed)
        
        # Create mock admin instance
        modeladmin = EmailAttachmentAdmin(EmailAttachment, None)
        
        # Call the admin action
        mark_as_processed(modeladmin, request, queryset)
        
        # Verify the attachment was marked as processed
        self.attachment2.refresh_from_db()
        self.assertTrue(self.attachment2.processed)

    def test_mark_multiple_as_processed(self):
        """Test marking multiple attachments as processed at once."""
        from email_integration.admin import mark_as_processed, EmailAttachmentAdmin
        
        # Create request
        request = self.factory.post('/admin/email_integration/emailattachment/')
        request.user = self.user
        
        # Create queryset with both attachments
        queryset = EmailAttachment.objects.all()
        
        # Create mock admin instance
        modeladmin = EmailAttachmentAdmin(EmailAttachment, None)
        
        # Call the admin action
        mark_as_processed(modeladmin, request, queryset)
        
        # Verify both attachments were marked as processed
        self.attachment1.refresh_from_db()
        self.attachment2.refresh_from_db()
        self.assertTrue(self.attachment1.processed)
        self.assertTrue(self.attachment2.processed)


class GeminiJSONParsingTests(TestCase):
    """Test cases for robust JSON parsing from Gemini API responses."""
    
    def test_parse_valid_json_with_markdown(self):
        """Test parsing valid JSON wrapped in markdown code blocks."""
        raw_response = '''```json
{
  "document_type": "invoice",
  "data": {
    "invoice_number": "INV-123",
    "total_amount": 100.50
  }
}
```'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(result["data"]["invoice_number"], "INV-123")
        self.assertEqual(result["data"]["total_amount"], 100.50)
    
    def test_parse_valid_json_without_markdown(self):
        """Test parsing valid JSON without markdown wrapper."""
        raw_response = '''{
  "document_type": "job_card",
  "data": {
    "job_card_number": "JC-456"
  }
}'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(result["document_type"], "job_card")
        self.assertEqual(result["data"]["job_card_number"], "JC-456")
    
    def test_parse_json_with_trailing_comma_in_object(self):
        """Test parsing JSON with trailing comma before closing brace."""
        raw_response = '''```json
{
  "document_type": "invoice",
  "data": {
    "invoice_number": "INV-123",
    "total_amount": 100.50,
  }
}
```'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(result["data"]["total_amount"], 100.50)
    
    def test_parse_json_with_trailing_comma_in_array(self):
        """Test parsing JSON with trailing comma in array."""
        raw_response = '''```json
{
  "document_type": "invoice",
  "data": {
    "line_items": [
      {"product": "Item 1"},
      {"product": "Item 2"},
    ]
  }
}
```'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(len(result["data"]["line_items"]), 2)
        self.assertEqual(result["data"]["line_items"][0]["product"], "Item 1")
    
    def test_parse_json_with_missing_brace_after_trailing_comma(self):
        """Test parsing JSON with missing closing brace after value and trailing comma."""
        # This simulates the exact error from the issue
        raw_response = '''```json
{
  "document_type": "invoice",
  "data": {
    "line_items": [
      {
        "product_code": "ABC-123",
        "quantity": 1,
        "total_amount": 749.00
      ,
      {
        "product_code": "DEF-456",
        "quantity": 2,
        "total_amount": 650.00
      }
    ]
  }
}
```'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(len(result["data"]["line_items"]), 2)
        self.assertEqual(result["data"]["line_items"][0]["product_code"], "ABC-123")
        self.assertEqual(result["data"]["line_items"][1]["product_code"], "DEF-456")
    
    def test_parse_json_with_text_before_and_after(self):
        """Test parsing JSON when there's extra text before/after the JSON object."""
        raw_response = '''Here is the analysis:
{
  "document_type": "invoice",
  "data": {
    "invoice_number": "INV-789"
  }
}
That's the complete data.'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(result["data"]["invoice_number"], "INV-789")
    
    def test_parse_empty_response_raises_error(self):
        """Test that empty response raises appropriate error."""
        with self.assertRaises(json.JSONDecodeError) as context:
            _parse_gemini_json_response("", "[Test]")
        self.assertIn("Empty response", str(context.exception))
    
    def test_parse_whitespace_only_response_raises_error(self):
        """Test that whitespace-only response raises appropriate error."""
        with self.assertRaises(json.JSONDecodeError) as context:
            _parse_gemini_json_response("   \n  \t  ", "[Test]")
        self.assertIn("Empty response", str(context.exception))
    
    def test_parse_completely_invalid_json(self):
        """Test that completely invalid JSON raises error with context."""
        raw_response = "This is not JSON at all, just random text."
        with self.assertRaises(json.JSONDecodeError) as context:
            _parse_gemini_json_response(raw_response, "[Test]")
        # Should contain information about all strategies failing
        self.assertIn("All parsing strategies failed", str(context.exception))
    
    def test_parse_actual_error_from_issue(self):
        """Test parsing the actual malformed JSON from the GitHub issue."""
        # Simplified version of the actual error from the issue
        raw_response = '''```json
{
  "document_type": "invoice",
  "data": {
    "issuer": {
      "name": "AV AVONDALE"
    },
    "line_items": [
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
    ],
    "invoice_number": "0",
    "customer_reference_no": "AV01/0036838",
    "total_amount": 2569.00
  }
}
```'''
        result = _parse_gemini_json_response(raw_response, "[Test]")
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(result["data"]["issuer"]["name"], "AV AVONDALE")
        self.assertEqual(len(result["data"]["line_items"]), 2)
        self.assertEqual(result["data"]["line_items"][0]["product_code"], "OB-MP-GB-920001211")
        self.assertEqual(result["data"]["line_items"][1]["product_code"], "OB-MP-GB-920001212")
        self.assertEqual(result["data"]["total_amount"], 2569.00)

