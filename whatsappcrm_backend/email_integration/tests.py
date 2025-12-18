from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch, MagicMock
import json

from .models import EmailAttachment
from .tasks import _create_order_from_invoice_data, parse_json_robust
from customer_data.models import CustomerProfile, Order, OrderItem, Contact
from products_and_services.models import Product


class ParseJsonRobustTests(TestCase):
    """Test cases for robust JSON parsing function."""

    def test_valid_json(self):
        """Test that valid JSON is parsed correctly."""
        valid_json = '{"name": "test", "value": 123}'
        result = parse_json_robust(valid_json)
        self.assertEqual(result, {"name": "test", "value": 123})

    def test_json_with_trailing_comma_in_object(self):
        """Test JSON with trailing comma in object."""
        json_with_trailing = '{"name": "test", "value": 123,}'
        result = parse_json_robust(json_with_trailing)
        self.assertEqual(result, {"name": "test", "value": 123})

    def test_json_with_trailing_comma_in_array(self):
        """Test JSON with trailing comma in array."""
        json_with_trailing = '{"items": [1, 2, 3,]}'
        result = parse_json_robust(json_with_trailing)
        self.assertEqual(result, {"items": [1, 2, 3]})

    def test_json_with_trailing_comma_multiline(self):
        """Test JSON with trailing comma on separate line (real-world Gemini case)."""
        json_with_trailing = """{
  "line_items": [
    {
      "product_code": "OB-MP-GB-920001211",
      "total_amount": 749.00
    ,
    {
      "product_code": "OB-MP-GB-920001212",
      "total_amount": 650.00
    }
  ]
}"""
        result = parse_json_robust(json_with_trailing)
        self.assertEqual(len(result["line_items"]), 2)
        self.assertEqual(result["line_items"][0]["total_amount"], 749.00)

    def test_json_with_single_line_comment(self):
        """Test JSON with single-line comment."""
        json_with_comment = '{"name": "test", // this is a comment\n"value": 123}'
        result = parse_json_robust(json_with_comment)
        self.assertEqual(result, {"name": "test", "value": 123})

    def test_json_with_multiline_comment(self):
        """Test JSON with multi-line comment."""
        json_with_comment = '{"name": "test", /* this is a \nmulti-line comment */ "value": 123}'
        result = parse_json_robust(json_with_comment)
        self.assertEqual(result, {"name": "test", "value": 123})

    def test_json_with_multiple_consecutive_commas(self):
        """Test JSON with multiple consecutive commas."""
        json_with_multiple = '{"items": [1,, 2, 3]}'
        result = parse_json_robust(json_with_multiple)
        self.assertEqual(result["items"], [1, 2, 3])

    def test_complex_nested_json_with_trailing_commas(self):
        """Test complex nested JSON with multiple trailing commas."""
        complex_json = """{
  "document_type": "invoice",
  "data": {
    "issuer": {
      "name": "Test Company",
      "email": "test@example.com",
    },
    "line_items": [
      {
        "description": "Item 1",
        "quantity": 1,
        "total": 100,
      },
      {
        "description": "Item 2",
        "quantity": 2,
        "total": 200,
      },
    ],
    "total_amount": 300,
  }
}"""
        result = parse_json_robust(complex_json)
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(len(result["data"]["line_items"]), 2)
        self.assertEqual(result["data"]["total_amount"], 300)

    def test_json_with_unescaped_newlines_in_strings(self):
        """Test JSON with unescaped newline characters within string values."""
        json_with_newlines = '{"text": "Line 1\nLine 2", "value": 123}'
        result = parse_json_robust(json_with_newlines)
        # After parsing, Python's json.loads will convert \\n back to \n
        self.assertEqual(result["text"], "Line 1\nLine 2")
        self.assertEqual(result["value"], 123)

    def test_empty_string_raises_error(self):
        """Test that empty string raises JSONDecodeError."""
        with self.assertRaises(json.JSONDecodeError):
            parse_json_robust("")

    def test_invalid_json_raises_error(self):
        """Test that truly invalid JSON still raises error."""
        with self.assertRaises(json.JSONDecodeError):
            parse_json_robust("not json at all {invalid]")

    def test_gemini_real_world_example(self):
        """Test with the exact error case from the issue."""
        gemini_response = """{
  "document_type": "invoice",
  "data": {
    "issuer": {
      "tin": "2000018528",
      "name": "AV AVONDALE"
    },
    "line_items": [
      {
        "product_code": "OB-MP-GB-920001211",
        "description": "SOLAR BATTERY DEYE SE-G5.1 100AH 51.2V 1P16S",
        "quantity": 1,
        "unit_price": 651.30,
        "vat_amount": 97.70,
        "total_amount": 749.00
      ,
      {
        "product_code": "OB-MP-GB-920001212",
        "description": "SOLAR INVERTER DEYE 6KW",
        "quantity": 1,
        "unit_price": 565.22,
        "vat_amount": 84.78,
        "total_amount": 650.00
      }
    ],
    "invoice_number": "0",
    "customer_reference_no": "AV01/0036838",
    "invoice_date": "2025-12-18",
    "total_amount": 2569.00
  }
}"""
        result = parse_json_robust(gemini_response)
        self.assertEqual(result["document_type"], "invoice")
        self.assertEqual(len(result["data"]["line_items"]), 2)
        self.assertEqual(result["data"]["line_items"][0]["total_amount"], 749.00)
        self.assertEqual(result["data"]["line_items"][1]["total_amount"], 650.00)


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
