from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import ZohoCredential
from .utils import ZohoClient


class ZohoCredentialModelTest(TestCase):
    """Tests for the ZohoCredential model."""
    
    def test_singleton_pattern(self):
        """Test that only one ZohoCredential instance can exist."""
        # Create first instance
        cred1 = ZohoCredential.objects.create(
            client_id='test_client_1',
            client_secret='test_secret_1'
        )
        
        # Create second instance
        cred2 = ZohoCredential.objects.create(
            client_id='test_client_2',
            client_secret='test_secret_2'
        )
        
        # Should only have one instance
        self.assertEqual(ZohoCredential.objects.count(), 1)
        
        # The second creation should have updated the first
        cred = ZohoCredential.objects.first()
        self.assertEqual(cred.client_id, 'test_client_2')
    
    def test_get_instance(self):
        """Test the get_instance class method."""
        # Should return None when no instance exists
        self.assertIsNone(ZohoCredential.get_instance())
        
        # Create instance
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret'
        )
        
        # Should return the instance
        instance = ZohoCredential.get_instance()
        self.assertIsNotNone(instance)
        self.assertEqual(instance.client_id, 'test_client')
    
    def test_is_expired_no_token(self):
        """Test is_expired when no token is set."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret'
        )
        
        # Should be expired if no token is set
        self.assertTrue(cred.is_expired())
    
    def test_is_expired_with_valid_token(self):
        """Test is_expired with a valid (non-expired) token."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            access_token='valid_token',
            expires_in=timezone.now() + timedelta(hours=1)
        )
        
        # Should not be expired
        self.assertFalse(cred.is_expired())
    
    def test_is_expired_with_expired_token(self):
        """Test is_expired with an expired token."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            access_token='expired_token',
            expires_in=timezone.now() - timedelta(hours=1)
        )
        
        # Should be expired
        self.assertTrue(cred.is_expired())
    
    def test_is_expired_near_expiration(self):
        """Test is_expired with token near expiration (within buffer)."""
        # Token expires in 3 minutes (within 5-minute buffer)
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            access_token='soon_expired_token',
            expires_in=timezone.now() + timedelta(minutes=3)
        )
        
        # Should be considered expired due to buffer
        self.assertTrue(cred.is_expired())


class ZohoClientURLNormalizationTest(TestCase):
    """Tests for ZohoClient URL construction and normalization."""
    
    def test_api_domain_with_trailing_slash(self):
        """Test that trailing slashes are properly removed from api_domain."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            api_domain='https://www.zohoapis.com/',
            organization_id='123456'
        )
        
        client = ZohoClient()
        # Should remove trailing slash
        self.assertEqual(client.api_base_url, 'https://www.zohoapis.com')
    
    def test_api_domain_with_inventory_suffix(self):
        """Test that /inventory suffix is properly removed from api_domain."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            api_domain='https://www.zohoapis.com/inventory',
            organization_id='123456'
        )
        
        client = ZohoClient()
        # Should remove /inventory suffix
        self.assertEqual(client.api_base_url, 'https://www.zohoapis.com')
    
    def test_api_domain_with_trailing_slash_and_inventory(self):
        """Test that both trailing slash and /inventory are removed."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            api_domain='https://www.zohoapis.com/inventory/',
            organization_id='123456'
        )
        
        client = ZohoClient()
        # Should remove both
        self.assertEqual(client.api_base_url, 'https://www.zohoapis.com')
    
    def test_api_domain_without_issues(self):
        """Test that clean api_domain remains unchanged."""
        cred = ZohoCredential.objects.create(
            client_id='test_client',
            client_secret='test_secret',
            api_domain='https://www.zohoapis.com',
            organization_id='123456'
        )
        
        client = ZohoClient()
        # Should remain unchanged
        self.assertEqual(client.api_base_url, 'https://www.zohoapis.com')
    
    def test_api_domain_alternate_regions(self):
        """Test URL normalization for different regional domains."""
        test_cases = [
            ('https://www.zohoapis.eu/', 'https://www.zohoapis.eu'),
            ('https://www.zohoapis.in/inventory', 'https://www.zohoapis.in'),
            ('https://www.zohoapis.com.au/inventory/', 'https://www.zohoapis.com.au'),
        ]
        
        for input_domain, expected_domain in test_cases:
            with self.subTest(input_domain=input_domain):
                # Update the existing credential
                cred = ZohoCredential.get_instance()
                if cred:
                    cred.api_domain = input_domain
                    cred.save()
                else:
                    cred = ZohoCredential.objects.create(
                        client_id='test_client',
                        client_secret='test_secret',
                        api_domain=input_domain,
                        organization_id='123456'
                    )
                
                client = ZohoClient()
                self.assertEqual(client.api_base_url, expected_domain)

