from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import ZohoCredential


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

