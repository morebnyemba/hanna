# whatsappcrm_backend/opensolar_integration/api_client.py

import requests
import logging
import time
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from .models import OpenSolarConfig

logger = logging.getLogger(__name__)


class OpenSolarAPIClient:
    """
    Client for interacting with OpenSolar API.
    """
    
    def __init__(self, config: Optional[OpenSolarConfig] = None):
        """
        Initialize API client with configuration.
        """
        if config is None:
            config = OpenSolarConfig.objects.filter(is_active=True).first()
            if not config:
                raise ValueError("No active OpenSolar configuration found")
        
        self.config = config
        self.base_url = config.api_base_url.rstrip('/')
        self.org_id = config.org_id
        self.headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json',
        }
        self.timeout = config.api_timeout
        self.retry_count = config.api_retry_count
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to OpenSolar API with retry logic.
        """
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"OpenSolar API {method} {url} (attempt {attempt + 1})")
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                logger.info(f"OpenSolar API {method} {url} - Success")
                # Return parsed JSON if content exists, otherwise empty dict
                return response.json() if response.content else {}
                
            except requests.exceptions.RequestException as e:
                logger.error(f"OpenSolar API {method} {url} - Error: {str(e)}")
                
                if attempt == self.retry_count - 1:
                    raise
                
                # Exponential backoff
                time.sleep(2 ** attempt)
        
        raise Exception("Max retries exceeded")
    
    # Project Methods
    
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project in OpenSolar.
        
        Args:
            project_data: Project details
            
        Returns:
            Created project data including project_id
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/"
        return self._make_request('POST', endpoint, data=project_data)
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project details from OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/{project_id}"
        return self._make_request('GET', endpoint)
    
    def update_project(
        self,
        project_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update project in OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/{project_id}"
        return self._make_request('PATCH', endpoint, data=update_data)
    
    def list_projects(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        List projects from OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/projects/"
        response = self._make_request('GET', endpoint, params=filters)
        return response.get('results', [])
    
    # Contact Methods
    
    def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new contact in OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/"
        return self._make_request('POST', endpoint, data=contact_data)
    
    def get_contact(self, contact_id: str) -> Dict[str, Any]:
        """
        Get contact details from OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/{contact_id}"
        return self._make_request('GET', endpoint)
    
    def update_contact(
        self,
        contact_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update contact in OpenSolar.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/{contact_id}"
        return self._make_request('PATCH', endpoint, data=update_data)
    
    def find_contact_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Find contact by phone number.
        """
        endpoint = f"/api/orgs/{self.org_id}/contacts/"
        response = self._make_request('GET', endpoint, params={'phone': phone})
        results = response.get('results', [])
        return results[0] if results else None
    
    # Webhook Methods
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """
        List all webhooks for the organization.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/"
        response = self._make_request('GET', endpoint)
        return response.get('results', [])
    
    def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new webhook.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/"
        return self._make_request('POST', endpoint, data=webhook_data)
    
    def update_webhook(
        self,
        webhook_id: str,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update webhook configuration.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/{webhook_id}"
        return self._make_request('PATCH', endpoint, data=update_data)
    
    def delete_webhook(self, webhook_id: str) -> None:
        """
        Delete a webhook.
        """
        endpoint = f"/api/orgs/{self.org_id}/webhooks/{webhook_id}"
        self._make_request('DELETE', endpoint)
    
    # Helper Methods
    
    def test_connection(self) -> bool:
        """
        Test API connectivity.
        """
        try:
            self.list_projects()
            return True
        except Exception as e:
            logger.error(f"OpenSolar API connection test failed: {str(e)}")
            return False
