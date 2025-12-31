"""
Utility classes for Zoho API integration.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
from django.utils import timezone
from datetime import timedelta

from .models import ZohoCredential

logger = logging.getLogger(__name__)


class ZohoClient:
    """
    Client for interacting with Zoho Inventory API.
    Handles OAuth token management and API calls.
    """

    def __init__(self):
        """Initialize the Zoho client with credentials from the database."""
        self.credentials = ZohoCredential.get_instance()
        if not self.credentials:
            raise ValueError("Zoho credentials not configured. Please add credentials in the admin panel.")
        
        self.token_url = "https://accounts.zoho.com/oauth/v2/token"
        self.api_base_url = self.credentials.api_domain

    def get_valid_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token
            
        Raises:
            Exception: If unable to get or refresh token
        """
        if not self.credentials.is_expired():
            logger.info("Using existing valid access token")
            return self.credentials.access_token
        
        logger.info("Access token expired or missing, refreshing...")
        return self._refresh_token()

    def _refresh_token(self) -> str:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            str: New access token
            
        Raises:
            Exception: If token refresh fails
        """
        if not self.credentials.refresh_token:
            raise ValueError("No refresh token available. Please re-authenticate with Zoho.")

        payload = {
            'refresh_token': self.credentials.refresh_token,
            'client_id': self.credentials.client_id,
            'client_secret': self.credentials.client_secret,
            'grant_type': 'refresh_token'
        }

        try:
            response = requests.post(self.token_url, data=payload, timeout=30)
            response.raise_for_status()
            token_data = response.json()

            if 'access_token' not in token_data:
                raise ValueError(f"Access token not in response: {token_data}")

            # Update credentials with new token
            self.credentials.access_token = token_data['access_token']
            
            # Calculate expiration time (default 1 hour if not provided)
            expires_in_seconds = token_data.get('expires_in', 3600)
            self.credentials.expires_in = timezone.now() + timedelta(seconds=expires_in_seconds)
            
            self.credentials.save(update_fields=['access_token', 'expires_in', 'updated_at'])
            
            logger.info("Successfully refreshed Zoho access token")
            return self.credentials.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh Zoho token: {str(e)}")
            raise Exception(f"Failed to refresh Zoho access token: {str(e)}")

    def fetch_products(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Fetch products (items) from Zoho Inventory.
        
        Args:
            page: Page number to fetch (1-indexed)
            per_page: Number of items per page (max 200)
            
        Returns:
            Dict containing:
                - items: List of product/item dictionaries
                - page_context: Pagination information
                
        Raises:
            Exception: If API call fails
        """
        token = self.get_valid_token()
        
        if not self.credentials.organization_id:
            raise ValueError("Organization ID not set in Zoho credentials")

        headers = {
            'Authorization': f'Zoho-oauthtoken {token}'
        }
        
        params = {
            'organization_id': self.credentials.organization_id,
            'page': page,
            'per_page': min(per_page, 200)  # Zoho max is 200
        }

        url = f"{self.api_base_url}/api/v1/items"

        try:
            logger.info(f"Fetching Zoho items page {page} with {per_page} items per page")
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data.get('code') != 0:
                error_msg = data.get('message', 'Unknown error')
                raise Exception(f"Zoho API error: {error_msg}")

            items = data.get('items', [])
            page_context = data.get('page_context', {})
            
            logger.info(f"Successfully fetched {len(items)} items from page {page}")
            
            return {
                'items': items,
                'page_context': page_context
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Zoho items: {str(e)}")
            raise Exception(f"Failed to fetch items from Zoho: {str(e)}")

    def fetch_all_products(self) -> List[Dict[str, Any]]:
        """
        Fetch all products from Zoho Inventory, handling pagination.
        
        Returns:
            List of all product dictionaries
            
        Raises:
            Exception: If API calls fail
        """
        all_items = []
        page = 1
        
        while True:
            result = self.fetch_products(page=page)
            items = result.get('items', [])
            
            if not items:
                break
                
            all_items.extend(items)
            
            page_context = result.get('page_context', {})
            has_more_page = page_context.get('has_more_page', False)
            
            if not has_more_page:
                break
                
            page += 1
            logger.info(f"Fetching next page ({page})...")

        logger.info(f"Fetched total of {len(all_items)} items from Zoho")
        return all_items
