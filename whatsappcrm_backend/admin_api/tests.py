# whatsappcrm_backend/admin_api/tests.py
"""
Tests for Admin API endpoints
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from customer_data.models import InstallationRequest, CustomerProfile
from conversations.models import Contact
from warranty.models import Technician


class AdminInstallationRequestAPITestCase(TestCase):
    """Test cases for Admin Installation Request API"""

    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        
        # Create non-admin user
        self.regular_user = User.objects.create_user(
            username='user',
            email='user@test.com',
            password='userpass123'
        )
        
        # Create technician user
        self.tech_user = User.objects.create_user(
            username='technician',
            email='tech@test.com',
            password='techpass123'
        )
        
        # Create a contact for customer profile
        self.contact = Contact.objects.create(
            whatsapp_id='1234567890',
            name='Test Contact',
            phone_number='+1234567890'
        )
        
        # Create customer profile
        self.customer = CustomerProfile.objects.create(
            contact=self.contact,
            first_name='John',
            last_name='Doe',
            email='john@test.com'
        )
        
        # Create technician
        self.technician = Technician.objects.create(
            user=self.tech_user,
            specialization='Solar Installation',
            contact_phone='+1234567890'
        )
        
        # Create installation request with dynamic date
        future_date = (timezone.now() + timedelta(days=5)).strftime('%Y-%m-%d %H:%M')
        self.installation = InstallationRequest.objects.create(
            customer=self.customer,
            status='pending',
            installation_type='solar',
            full_name='John Doe',
            address='123 Test Street',
            contact_phone='+1234567890',
            preferred_datetime=future_date,
        )
        
        # Set up API client
        self.client = APIClient()

    def test_list_installations_as_admin(self):
        """Test listing installations as admin user"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/crm-api/admin-panel/installation-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_list_installations_as_non_admin(self):
        """Test listing installations as non-admin user (should fail)"""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/crm-api/admin-panel/installation-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_installation_as_admin(self):
        """Test retrieving a specific installation as admin"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.installation.id)
        self.assertEqual(response.data['full_name'], 'John Doe')
        self.assertEqual(response.data['status'], 'pending')

    def test_create_installation_as_admin(self):
        """Test creating a new installation request as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Use dynamic date for test
        future_date = (timezone.now() + timedelta(days=10)).strftime('%Y-%m-%d %H:%M')
        
        data = {
            'customer': self.customer.pk,
            'status': 'pending',
            'installation_type': 'starlink',
            'full_name': 'Jane Smith',
            'address': '456 Another Street',
            'contact_phone': '+9876543210',
            'preferred_datetime': future_date,
        }
        
        response = self.client.post(
            '/crm-api/admin-panel/installation-requests/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['full_name'], 'Jane Smith')
        self.assertEqual(response.data['installation_type'], 'starlink')

    def test_update_installation_as_admin(self):
        """Test updating an installation request as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Use dynamic date for test
        future_date = (timezone.now() + timedelta(days=8)).strftime('%Y-%m-%d %H:%M')
        
        data = {
            'customer': self.customer.pk,
            'status': 'scheduled',
            'installation_type': 'solar',
            'full_name': 'John Doe Updated',
            'address': '123 Test Street',
            'contact_phone': '+1234567890',
            'preferred_datetime': future_date,
        }
        
        response = self.client.put(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['full_name'], 'John Doe Updated')
        self.assertEqual(response.data['status'], 'scheduled')

    def test_delete_installation_as_admin(self):
        """Test deleting an installation request as admin"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.delete(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify it's deleted
        self.assertFalse(
            InstallationRequest.objects.filter(id=self.installation.id).exists()
        )

    def test_mark_completed_action(self):
        """Test marking installation as completed via custom action"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.post(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/mark_completed/'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['data']['status'], 'completed')
        
        # Verify in database
        self.installation.refresh_from_db()
        self.assertEqual(self.installation.status, 'completed')

    def test_assign_technicians_action(self):
        """Test assigning technicians to installation via custom action"""
        self.client.force_authenticate(user=self.admin_user)
        
        data = {
            'technician_ids': [self.technician.id]
        }
        
        response = self.client.post(
            f'/crm-api/admin-panel/installation-requests/{self.installation.id}/assign_technicians/',
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify technician was assigned
        self.installation.refresh_from_db()
        self.assertEqual(self.installation.technicians.count(), 1)
        self.assertEqual(self.installation.technicians.first().id, self.technician.id)

    def test_filter_by_status(self):
        """Test filtering installations by status"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Create another installation with different status and dynamic date
        future_date = (timezone.now() + timedelta(days=3)).strftime('%Y-%m-%d %H:%M')
        InstallationRequest.objects.create(
            customer=self.customer,
            status='completed',
            installation_type='solar',
            full_name='Jane Doe',
            address='789 Another Street',
            contact_phone='+1111111111',
            preferred_datetime=future_date,
        )
        
        response = self.client.get(
            '/crm-api/admin-panel/installation-requests/?status=pending'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'pending')

    def test_search_installations(self):
        """Test searching installations"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get(
            '/crm-api/admin-panel/installation-requests/?search=John'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the API"""
        response = self.client.get('/crm-api/admin-panel/installation-requests/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
