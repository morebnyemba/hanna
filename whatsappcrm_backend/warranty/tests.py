from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from warranty.models import Warranty, WarrantyClaim, Manufacturer, Technician
from customer_data.models import CustomerProfile, Order
from conversations.models import Contact
from products_and_services.models import Product, SerializedItem
from installation_systems.models import (
    InstallationSystemRecord, 
    CommissioningChecklistTemplate,
    InstallationChecklistEntry,
    InstallationPhoto
)
from warranty.pdf_utils import WarrantyCertificateGenerator, InstallationReportGenerator

User = get_user_model()


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

