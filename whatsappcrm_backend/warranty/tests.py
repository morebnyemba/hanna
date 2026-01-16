from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from warranty.models import (
    Warranty, WarrantyClaim, Manufacturer, Technician,
    WarrantyRule, SLAThreshold, SLAStatus
)
from warranty.services import WarrantyRuleService, SLAService
from customer_data.models import CustomerProfile, Order, InstallationRequest
from conversations.models import Contact
from products_and_services.models import Product, SerializedItem, ProductCategory
from installation_systems.models import (
    InstallationSystemRecord, 
    CommissioningChecklistTemplate,
    InstallationChecklistEntry,
    InstallationPhoto
)
from warranty.pdf_utils import WarrantyCertificateGenerator, InstallationReportGenerator

User = get_user_model()


class WarrantyRuleModelTests(TestCase):
    """Test WarrantyRule model and validation"""
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(
            name='Solar Panels'
        )
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='hardware',
            price=Decimal('150.00'),
            category=self.category
        )
    
    def test_create_product_warranty_rule(self):
        """Test creating a warranty rule for a specific product"""
        rule = WarrantyRule.objects.create(
            name='Solar Panel Standard Warranty',
            product=self.product,
            warranty_duration_days=365,
            is_active=True,
            priority=1
        )
        
        self.assertEqual(rule.warranty_duration_days, 365)
        self.assertTrue(rule.is_active)
        self.assertEqual(rule.product, self.product)
        self.assertIsNone(rule.product_category)
    
    def test_create_category_warranty_rule(self):
        """Test creating a warranty rule for a product category"""
        rule = WarrantyRule.objects.create(
            name='Solar Category Warranty',
            product_category=self.category,
            warranty_duration_days=730,
            is_active=True,
            priority=1
        )
        
        self.assertEqual(rule.warranty_duration_days, 730)
        self.assertEqual(rule.product_category, self.category)
        self.assertIsNone(rule.product)
    
    def test_warranty_rule_str_representation(self):
        """Test string representation of warranty rule"""
        rule = WarrantyRule.objects.create(
            name='Test Rule',
            product=self.product,
            warranty_duration_days=365,
            is_active=True
        )
        
        self.assertIn('Test Rule', str(rule))
        self.assertIn('Solar Panel 100W', str(rule))
        self.assertIn('365', str(rule))


class WarrantyRuleServiceTests(TestCase):
    """Test WarrantyRuleService business logic"""
    
    def setUp(self):
        """Set up test data"""
        self.category = ProductCategory.objects.create(name='Solar Panels')
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='hardware',
            price=Decimal('150.00'),
            category=self.category
        )
        
        # Create contact and customer
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer'
        )
        
        # Create serialized item
        self.serialized_item = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN123456789',
            status='sold'
        )
    
    def test_find_product_specific_rule(self):
        """Test finding a product-specific warranty rule"""
        # Create rules
        product_rule = WarrantyRule.objects.create(
            name='Product Specific Rule',
            product=self.product,
            warranty_duration_days=365,
            is_active=True,
            priority=10
        )
        
        category_rule = WarrantyRule.objects.create(
            name='Category Rule',
            product_category=self.category,
            warranty_duration_days=730,
            is_active=True,
            priority=5
        )
        
        # Product-specific rule should take precedence
        found_rule = WarrantyRuleService.find_applicable_rule(self.product)
        
        self.assertEqual(found_rule, product_rule)
        self.assertEqual(found_rule.warranty_duration_days, 365)
    
    def test_find_category_rule(self):
        """Test finding a category-based warranty rule"""
        # Create only category rule
        category_rule = WarrantyRule.objects.create(
            name='Category Rule',
            product_category=self.category,
            warranty_duration_days=730,
            is_active=True,
            priority=5
        )
        
        found_rule = WarrantyRuleService.find_applicable_rule(self.product)
        
        self.assertEqual(found_rule, category_rule)
        self.assertEqual(found_rule.warranty_duration_days, 730)
    
    def test_no_applicable_rule(self):
        """Test when no warranty rule is found"""
        found_rule = WarrantyRuleService.find_applicable_rule(self.product)
        
        self.assertIsNone(found_rule)
    
    def test_apply_rule_to_warranty(self):
        """Test applying a warranty rule to a warranty"""
        # Create rule
        rule = WarrantyRule.objects.create(
            name='Test Rule',
            product=self.product,
            warranty_duration_days=365,
            is_active=True
        )
        
        # Create warranty with same start and end date
        start_date = datetime.now().date()
        warranty = Warranty.objects.create(
            serialized_item=self.serialized_item,
            customer=self.customer,
            start_date=start_date,
            end_date=start_date  # Same as start, should trigger rule application
        )
        
        # Apply rule
        applied_rule, was_applied = WarrantyRuleService.apply_rule_to_warranty(warranty)
        
        self.assertTrue(was_applied)
        self.assertEqual(applied_rule, rule)
        
        # Reload warranty from database
        warranty.refresh_from_db()
        expected_end_date = start_date + timedelta(days=365)
        self.assertEqual(warranty.end_date, expected_end_date)
    
    def test_calculate_warranty_end_date(self):
        """Test calculating warranty end date"""
        # Create rule
        rule = WarrantyRule.objects.create(
            name='Test Rule',
            product=self.product,
            warranty_duration_days=365,
            is_active=True
        )
        
        start_date = datetime.now().date()
        end_date = WarrantyRuleService.calculate_warranty_end_date(self.product, start_date)
        
        expected_end_date = start_date + timedelta(days=365)
        self.assertEqual(end_date, expected_end_date)


class WarrantyCertificatePDFTests(APITestCase):
    """Test warranty certificate PDF generation"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        # Create contact and customer profile
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@customer.com',
            user=self.customer_user
        )
        
        # Create manufacturer
        self.manufacturer = Manufacturer.objects.create(
            name='Test Manufacturer',
            contact_email='manufacturer@test.com'
        )
        
        # Create product and serialized item
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='product',
            price=Decimal('150.00')
        )
        self.serialized_item = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN123456789',
            barcode='BC123456789',
            status='sold'
        )
        
        # Create warranty
        self.warranty = Warranty.objects.create(
            manufacturer=self.manufacturer,
            serialized_item=self.serialized_item,
            customer=self.customer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=365)).date(),
            status='active'
        )
        
        self.client = APIClient()
    
    def test_warranty_certificate_generation_by_admin(self):
        """Test warranty certificate PDF generation by admin user"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('warranty_api:warranty_certificate_pdf', kwargs={'warranty_id': self.warranty.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'warranty_certificate_{self.warranty.id}', response['Content-Disposition'])
        
        # Check that PDF data is not empty
        self.assertGreater(len(response.content), 0)
    
    def test_warranty_certificate_generation_by_customer(self):
        """Test warranty certificate PDF generation by customer (owner)"""
        self.client.force_authenticate(user=self.customer_user)
        
        url = reverse('warranty_api:warranty_certificate_pdf', kwargs={'warranty_id': self.warranty.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_warranty_certificate_unauthorized_customer(self):
        """Test warranty certificate access denied for unauthorized customer"""
        # Create another customer user
        other_user = User.objects.create_user(
            username='other_customer',
            email='other@test.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=other_user)
        
        url = reverse('warranty_api:warranty_certificate_pdf', kwargs={'warranty_id': self.warranty.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_warranty_certificate_unauthenticated(self):
        """Test warranty certificate requires authentication"""
        url = reverse('warranty_api:warranty_certificate_pdf', kwargs={'warranty_id': self.warranty.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_warranty_certificate_not_found(self):
        """Test warranty certificate with non-existent warranty ID"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('warranty_api:warranty_certificate_pdf', kwargs={'warranty_id': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_warranty_certificate_caching(self):
        """Test that warranty certificate PDFs are cached"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('warranty_api:warranty_certificate_pdf', kwargs={'warranty_id': self.warranty.id})
        
        # First request - generates PDF
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        content1 = response1.content
        
        # Second request - should get cached PDF
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        content2 = response2.content
        
        # Content should be identical (cached)
        self.assertEqual(content1, content2)


class InstallationReportPDFTests(APITestCase):
    """Test installation report PDF generation"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.tech_user = User.objects.create_user(
            username='technician',
            email='tech@test.com',
            password='testpass123'
        )
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@test.com',
            password='testpass123'
        )
        
        # Create contact and customer profile
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@customer.com',
            user=self.customer_user
        )
        
        # Create technician
        self.technician = Technician.objects.create(
            user=self.tech_user,
            technician_type='installer',
            specialization='Solar'
        )
        
        # Create product and serialized item
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='product',
            price=Decimal('150.00')
        )
        self.serialized_item = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN123456789',
            status='installed'
        )
        
        # Create installation system record
        self.installation = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
            system_classification='residential',
            installation_status='commissioned',
            installation_date=datetime.now().date(),
            commissioning_date=datetime.now().date(),
            installation_address='123 Test Street, Harare'
        )
        self.installation.technicians.add(self.technician)
        self.installation.installed_components.add(self.serialized_item)
        
        self.client = APIClient()
    
    def test_installation_report_generation_by_admin(self):
        """Test installation report PDF generation by admin user"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': self.installation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn(f'installation_report_{self.installation.id}', response['Content-Disposition'])
        
        # Check that PDF data is not empty
        self.assertGreater(len(response.content), 0)
    
    def test_installation_report_generation_by_technician(self):
        """Test installation report PDF generation by assigned technician"""
        self.client.force_authenticate(user=self.tech_user)
        
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': self.installation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_installation_report_generation_by_customer(self):
        """Test installation report PDF generation by customer (owner)"""
        self.client.force_authenticate(user=self.customer_user)
        
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': self.installation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'application/pdf')
    
    def test_installation_report_unauthorized_technician(self):
        """Test installation report access denied for unauthorized technician"""
        # Create another technician user
        other_tech_user = User.objects.create_user(
            username='other_tech',
            email='other_tech@test.com',
            password='testpass123'
        )
        other_tech = Technician.objects.create(
            user=other_tech_user,
            technician_type='installer'
        )
        
        self.client.force_authenticate(user=other_tech_user)
        
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': self.installation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_installation_report_unauthenticated(self):
        """Test installation report requires authentication"""
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': self.installation.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_installation_report_not_found(self):
        """Test installation report with non-existent installation ID"""
        self.client.force_authenticate(user=self.admin_user)
        
        fake_uuid = uuid.uuid4()
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': fake_uuid})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_installation_report_caching(self):
        """Test that installation report PDFs are cached"""
        self.client.force_authenticate(user=self.admin_user)
        
        url = reverse('warranty_api:installation_report_pdf', kwargs={'installation_id': self.installation.id})
        
        # First request - generates PDF
        response1 = self.client.get(url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        content1 = response1.content
        
        # Second request - should get cached PDF
        response2 = self.client.get(url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        content2 = response2.content
        
        # Content should be identical (cached)
        self.assertEqual(content1, content2)


class PDFGeneratorUnitTests(TestCase):
    """Unit tests for PDF generator classes"""
    
    def setUp(self):
        """Set up test data"""
        # Create contact and customer profile
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@customer.com'
        )
        
        # Create manufacturer
        self.manufacturer = Manufacturer.objects.create(
            name='Test Manufacturer',
            contact_email='manufacturer@test.com'
        )
        
        # Create product and serialized item
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='product',
            price=Decimal('150.00')
        )
        self.serialized_item = SerializedItem.objects.create(
            product=self.product,
            serial_number='SN123456789',
            status='sold'
        )
        
        # Create warranty
        self.warranty = Warranty.objects.create(
            manufacturer=self.manufacturer,
            serialized_item=self.serialized_item,
            customer=self.customer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=365)).date(),
            status='active'
        )
        
        # Create installation
        self.installation = InstallationSystemRecord.objects.create(
            customer=self.customer,
            installation_type='solar',
            system_size=Decimal('5.0'),
            capacity_unit='kW',
            system_classification='residential',
            installation_status='commissioned',
            installation_date=datetime.now().date(),
            commissioning_date=datetime.now().date(),
            installation_address='123 Test Street, Harare'
        )
    
    def test_warranty_certificate_generator_creates_pdf(self):
        """Test that warranty certificate generator creates valid PDF"""
        generator = WarrantyCertificateGenerator()
        pdf_buffer = generator.generate(self.warranty)
        
        # Check that buffer is not empty
        self.assertIsNotNone(pdf_buffer)
        pdf_data = pdf_buffer.getvalue()
        self.assertGreater(len(pdf_data), 0)
        
        # Check PDF header signature
        self.assertTrue(pdf_data.startswith(b'%PDF'))
    
    def test_installation_report_generator_creates_pdf(self):
        """Test that installation report generator creates valid PDF"""
        generator = InstallationReportGenerator()
        pdf_buffer = generator.generate(self.installation)
        
        # Check that buffer is not empty
        self.assertIsNotNone(pdf_buffer)
        pdf_data = pdf_buffer.getvalue()
        self.assertGreater(len(pdf_data), 0)
        
        # Check PDF header signature
        self.assertTrue(pdf_data.startswith(b'%PDF'))
    
    def test_qr_code_generation(self):
        """Test QR code generation"""
        generator = WarrantyCertificateGenerator()
        qr_image = generator.generate_qr_code('https://test.com', size=100)
        
        # Check that QR image was created
        self.assertIsNotNone(qr_image)


class SLAThresholdModelTests(TestCase):
    """Test SLAThreshold model"""
    
    def test_create_sla_threshold(self):
        """Test creating an SLA threshold"""
        sla = SLAThreshold.objects.create(
            name='Installation SLA',
            request_type='installation',
            response_time_hours=24,
            resolution_time_hours=72,
            notification_threshold_percent=80,
            is_active=True
        )
        
        self.assertEqual(sla.request_type, 'installation')
        self.assertEqual(sla.response_time_hours, 24)
        self.assertEqual(sla.resolution_time_hours, 72)
        self.assertTrue(sla.is_active)
    
    def test_sla_threshold_str_representation(self):
        """Test string representation of SLA threshold"""
        sla = SLAThreshold.objects.create(
            name='Warranty Claim SLA',
            request_type='warranty_claim',
            response_time_hours=48,
            resolution_time_hours=120
        )
        
        self.assertIn('Warranty Claim SLA', str(sla))
        self.assertIn('48h', str(sla))
        self.assertIn('120h', str(sla))


class SLAServiceTests(TestCase):
    """Test SLAService business logic"""
    
    def setUp(self):
        """Set up test data"""
        # Create SLA threshold
        self.sla_threshold = SLAThreshold.objects.create(
            name='Installation SLA',
            request_type='installation',
            response_time_hours=24,
            resolution_time_hours=72,
            notification_threshold_percent=80,
            is_active=True
        )
        
        # Create customer
        self.contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='Test',
            last_name='Customer',
            email='test@customer.com'
        )
        
        # Create installation request
        self.installation_request = InstallationRequest.objects.create(
            customer=self.customer,
            status='pending',
            installation_type='solar',
            full_name='Test Customer'
        )
    
    def test_get_sla_threshold_for_request(self):
        """Test getting SLA threshold for a request type"""
        threshold = SLAService.get_sla_threshold_for_request('installation')
        
        self.assertEqual(threshold, self.sla_threshold)
        self.assertEqual(threshold.response_time_hours, 24)
    
    def test_create_sla_status(self):
        """Test creating SLA status for a request"""
        created_at = datetime.now()
        
        sla_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation',
            created_at=created_at
        )
        
        self.assertIsNotNone(sla_status)
        self.assertEqual(sla_status.sla_threshold, self.sla_threshold)
        self.assertEqual(sla_status.request_created_at, created_at)
        
        # Check deadlines
        expected_response_deadline = created_at + timedelta(hours=24)
        expected_resolution_deadline = created_at + timedelta(hours=72)
        
        self.assertEqual(sla_status.response_time_deadline, expected_response_deadline)
        self.assertEqual(sla_status.resolution_time_deadline, expected_resolution_deadline)
    
    def test_mark_response_completed(self):
        """Test marking response as completed"""
        # Create SLA status
        sla_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation'
        )
        
        # Mark response completed
        updated_status = SLAService.mark_response_completed(self.installation_request)
        
        self.assertIsNotNone(updated_status.response_completed_at)
    
    def test_mark_resolution_completed(self):
        """Test marking resolution as completed"""
        # Create SLA status
        sla_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation'
        )
        
        # Mark resolution completed
        updated_status = SLAService.mark_resolution_completed(self.installation_request)
        
        self.assertIsNotNone(updated_status.resolution_completed_at)
    
    def test_get_sla_status(self):
        """Test getting SLA status for a request"""
        # Create SLA status
        created_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation'
        )
        
        # Get SLA status
        retrieved_status = SLAService.get_sla_status(self.installation_request)
        
        self.assertEqual(retrieved_status.id, created_status.id)
    
    def test_sla_compliance_metrics(self):
        """Test getting SLA compliance metrics"""
        # Create multiple SLA statuses
        for i in range(5):
            contact = Contact.objects.create(
                whatsapp_id=f'26377123456{i}',
                name=f'Customer {i}'
            )
            customer = CustomerProfile.objects.create(
                contact=contact,
                first_name=f'Customer{i}',
                last_name='Test'
            )
            request = InstallationRequest.objects.create(
                customer=customer,
                status='pending',
                installation_type='solar',
                full_name=f'Customer {i}'
            )
            SLAService.create_sla_status(
                request_object=request,
                request_type='installation'
            )
        
        # Get metrics
        metrics = SLAService.get_sla_compliance_metrics()
        
        self.assertEqual(metrics['total_requests'], 5)
        self.assertIn('response_compliant', metrics)
        self.assertIn('resolution_compliant', metrics)
        self.assertIn('overall_compliance_rate', metrics)


class SLAStatusModelTests(TestCase):
    """Test SLAStatus model and status updates"""
    
    def setUp(self):
        """Set up test data"""
        # Create SLA threshold
        self.sla_threshold = SLAThreshold.objects.create(
            name='Test SLA',
            request_type='installation',
            response_time_hours=24,
            resolution_time_hours=72,
            notification_threshold_percent=80
        )
        
        # Create customer and request
        contact = Contact.objects.create(
            whatsapp_id='263771234567',
            name='Test Customer'
        )
        customer = CustomerProfile.objects.create(
            contact=contact,
            first_name='Test',
            last_name='Customer'
        )
        self.installation_request = InstallationRequest.objects.create(
            customer=customer,
            status='pending',
            installation_type='solar',
            full_name='Test Customer'
        )
    
    def test_sla_status_compliant(self):
        """Test SLA status is compliant when within deadlines"""
        # Create recent SLA status
        sla_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation'
        )
        
        # Update status
        sla_status.update_status()
        
        # Should be compliant since just created
        self.assertEqual(sla_status.response_status, SLAStatus.StatusType.COMPLIANT)
        self.assertEqual(sla_status.resolution_status, SLAStatus.StatusType.COMPLIANT)
    
    def test_sla_status_breached(self):
        """Test SLA status breached when past deadline"""
        # Create SLA status with past deadline
        past_time = datetime.now() - timedelta(days=5)
        sla_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation',
            created_at=past_time
        )
        
        # Update status
        sla_status.update_status()
        
        # Should be breached since created 5 days ago
        self.assertEqual(sla_status.response_status, SLAStatus.StatusType.BREACHED)
        self.assertEqual(sla_status.resolution_status, SLAStatus.StatusType.BREACHED)
    
    def test_should_send_notification(self):
        """Test notification sending logic"""
        # Create SLA status
        sla_status = SLAService.create_sla_status(
            request_object=self.installation_request,
            request_type='installation',
            created_at=datetime.now() - timedelta(days=5)
        )
        
        # Update status to breached
        sla_status.update_status()
        
        # Should send notification
        self.assertTrue(sla_status.should_send_notification())


class WarrantyRuleAPITests(APITestCase):
    """Test Warranty Rule API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.category = ProductCategory.objects.create(name='Solar Panels')
        self.product = Product.objects.create(
            name='Solar Panel 100W',
            sku='SP-100W',
            product_type='hardware',
            price=Decimal('150.00'),
            category=self.category
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_create_warranty_rule(self):
        """Test creating a warranty rule via API"""
        url = reverse('admin_api:warranty-rule-list')
        data = {
            'name': 'Test Warranty Rule',
            'product': self.product.id,
            'warranty_duration_days': 365,
            'is_active': True,
            'priority': 1
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WarrantyRule.objects.count(), 1)
        
        rule = WarrantyRule.objects.first()
        self.assertEqual(rule.name, 'Test Warranty Rule')
        self.assertEqual(rule.warranty_duration_days, 365)
    
    def test_list_warranty_rules(self):
        """Test listing warranty rules via API"""
        # Create rules
        WarrantyRule.objects.create(
            name='Rule 1',
            product=self.product,
            warranty_duration_days=365,
            is_active=True
        )
        WarrantyRule.objects.create(
            name='Rule 2',
            product_category=self.category,
            warranty_duration_days=730,
            is_active=True
        )
        
        url = reverse('admin_api:warranty-rule-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_update_warranty_rule(self):
        """Test updating a warranty rule via API"""
        rule = WarrantyRule.objects.create(
            name='Test Rule',
            product=self.product,
            warranty_duration_days=365,
            is_active=True
        )
        
        url = reverse('admin_api:warranty-rule-detail', kwargs={'pk': rule.id})
        data = {
            'name': 'Updated Rule',
            'product': self.product.id,
            'warranty_duration_days': 730,
            'is_active': False,
            'priority': 5
        }
        
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        rule.refresh_from_db()
        self.assertEqual(rule.name, 'Updated Rule')
        self.assertEqual(rule.warranty_duration_days, 730)
        self.assertFalse(rule.is_active)
    
    def test_delete_warranty_rule(self):
        """Test deleting a warranty rule via API"""
        rule = WarrantyRule.objects.create(
            name='Test Rule',
            product=self.product,
            warranty_duration_days=365,
            is_active=True
        )
        
        url = reverse('admin_api:warranty-rule-detail', kwargs={'pk': rule.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WarrantyRule.objects.count(), 0)


class SLAThresholdAPITests(APITestCase):
    """Test SLA Threshold API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)
    
    def test_create_sla_threshold(self):
        """Test creating an SLA threshold via API"""
        url = reverse('admin_api:sla-threshold-list')
        data = {
            'name': 'Installation SLA',
            'request_type': 'installation',
            'response_time_hours': 24,
            'resolution_time_hours': 72,
            'notification_threshold_percent': 80,
            'is_active': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SLAThreshold.objects.count(), 1)
        
        sla = SLAThreshold.objects.first()
        self.assertEqual(sla.name, 'Installation SLA')
        self.assertEqual(sla.response_time_hours, 24)
    
    def test_list_sla_thresholds(self):
        """Test listing SLA thresholds via API"""
        SLAThreshold.objects.create(
            name='Installation SLA',
            request_type='installation',
            response_time_hours=24,
            resolution_time_hours=72
        )
        SLAThreshold.objects.create(
            name='Warranty Claim SLA',
            request_type='warranty_claim',
            response_time_hours=48,
            resolution_time_hours=120
        )
        
        url = reverse('admin_api:sla-threshold-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_sla_compliance_metrics_endpoint(self):
        """Test SLA compliance metrics endpoint"""
        url = reverse('admin_api:sla-status-compliance-metrics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_requests', response.data)
        self.assertIn('overall_compliance_rate', response.data)
