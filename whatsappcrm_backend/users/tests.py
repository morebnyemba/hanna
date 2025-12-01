from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework import status

from .models import Retailer

User = get_user_model()


class RetailerRegistrationTestCase(TestCase):
    """
    Test cases for retailer registration API.
    """
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
        self.register_url = '/crm-api/users/retailer/register/'

    def test_retailer_registration_success(self):
        """Test successful retailer registration."""
        data = {
            'email': 'retailer@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'Doe Electronics',
            'business_registration_number': 'REG-12345',
            'contact_phone': '+1234567890',
            'address': '123 Main St, City'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('retailer', response.data)
        
        # Verify user was created
        user = User.objects.get(email='retailer@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        
        # Verify retailer profile was created
        retailer = Retailer.objects.get(user=user)
        self.assertEqual(retailer.company_name, 'Doe Electronics')
        self.assertEqual(retailer.business_registration_number, 'REG-12345')
        
        # Verify user is in Retailer group
        self.assertTrue(user.groups.filter(name='Retailer').exists())

    def test_retailer_registration_missing_required_fields(self):
        """Test registration fails with missing required fields."""
        data = {
            'email': 'retailer@example.com',
            'password': 'SecurePass123!'
            # Missing first_name, last_name, company_name
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retailer_registration_duplicate_email(self):
        """Test registration fails with duplicate email."""
        # Create existing user
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='pass123'
        )
        
        data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'Doe Electronics'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_retailer_registration_duplicate_business_number(self):
        """Test registration fails with duplicate business registration number."""
        # Create existing retailer
        user = User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='pass123'
        )
        Retailer.objects.create(
            user=user,
            company_name='Existing Company',
            business_registration_number='REG-12345'
        )
        
        data = {
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'Doe Electronics',
            'business_registration_number': 'REG-12345'  # Duplicate
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RetailerProfileTestCase(TestCase):
    """
    Test cases for retailer profile management.
    """
    
    def setUp(self):
        """Set up test client and retailer."""
        self.client = APIClient()
        
        # Create retailer user
        self.user = User.objects.create_user(
            username='retailer@example.com',
            email='retailer@example.com',
            password='testpass123',
            first_name='John',
            last_name='Doe'
        )
        self.retailer = Retailer.objects.create(
            user=self.user,
            company_name='Test Electronics',
            business_registration_number='REG-TEST-001',
            contact_phone='+1234567890',
            address='123 Test St'
        )
        
        # Add to Retailer group
        retailer_group, _ = Group.objects.get_or_create(name='Retailer')
        self.user.groups.add(retailer_group)
        
        self.client.force_authenticate(user=self.user)

    def test_get_my_profile(self):
        """Test retailer can get their own profile."""
        response = self.client.get('/crm-api/users/retailers/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'Test Electronics')
        self.assertEqual(response.data['business_registration_number'], 'REG-TEST-001')

    def test_update_my_profile(self):
        """Test retailer can update their own profile."""
        data = {
            'company_name': 'Updated Electronics',
            'contact_phone': '+9876543210'
        }
        
        response = self.client.patch('/crm-api/users/retailers/me/update/', data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['company_name'], 'Updated Electronics')
        self.assertEqual(response.data['contact_phone'], '+9876543210')

    def test_list_retailers_as_admin(self):
        """Test admin can list all retailers."""
        admin_user = User.objects.create_superuser(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123'
        )
        self.client.force_authenticate(user=admin_user)
        
        response = self.client.get('/crm-api/users/retailers/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Response is paginated, so check for 'results' key
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertGreaterEqual(len(response.data['results']), 1)
        else:
            self.assertIsInstance(response.data, list)
            self.assertGreaterEqual(len(response.data), 1)

    def test_unauthenticated_cannot_access_profile(self):
        """Test unauthenticated users cannot access retailer profile."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/crm-api/users/retailers/me/')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
