"""
Utility classes for Zoho API integration.
"""
import logging
import requests
from typing import Dict, List, Optional, Any
from django.utils import timezone
from datetime import timedelta
from json import JSONDecodeError

from .models import ZohoCredential

logger = logging.getLogger(__name__)

# Constants for error message truncation
MAX_ERROR_RESPONSE_LENGTH = 500
MAX_ERROR_MESSAGE_LENGTH = 200


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
        
        # Log initialization details for debugging
        logger.info(
            f"ZohoClient initialized with organization_id: {self.credentials.organization_id}, "
            f"api_domain: {self.api_base_url}"
        )
    
    @classmethod
    def exchange_code_for_tokens(cls, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange an authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from Zoho OAuth callback
            redirect_uri: The redirect URI used in the authorization request
            
        Returns:
            Dict containing token data from Zoho
            
        Raises:
            ValueError: If credentials not configured
            Exception: If token exchange fails
        """
        credentials = ZohoCredential.get_instance()
        if not credentials:
            raise ValueError("Zoho credentials not configured")
        
        token_url = "https://accounts.zoho.com/oauth/v2/token"
        payload = {
            'code': code,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(token_url, data=payload, timeout=30)
            response.raise_for_status()
            token_data = response.json()
            
            if 'error' in token_data:
                raise Exception(f"Zoho token error: {token_data.get('error')}")
            
            if 'access_token' not in token_data:
                raise Exception("Access token not in response")
            
            # Update credentials
            credentials.access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                credentials.refresh_token = token_data['refresh_token']
            
            expires_in_seconds = token_data.get('expires_in', 3600)
            credentials.expires_in = timezone.now() + timedelta(seconds=expires_in_seconds)
            
            credentials.save()
            
            logger.info("Successfully exchanged authorization code for tokens")
            return token_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for tokens: {str(e)}")
            raise Exception(f"Failed to exchange authorization code: {str(e)}")

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
            ValueError: If organization_id is not set in credentials
            Exception: If API call fails, with detailed error message from Zoho
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

        url = f"{self.api_base_url}/inventory/v1/items"

        try:
            logger.info(
                f"Fetching Zoho items page {page} with {per_page} items per page. "
                f"URL: {url}, Organization ID: {self.credentials.organization_id}"
            )
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Check for HTTP errors and capture response body for better error messages
            if response.status_code != 200:
                error_details = {
                    'status_code': response.status_code,
                    'url': response.url,
                    'reason': response.reason
                }
                
                # Try to get JSON error from Zoho
                try:
                    error_json = response.json()
                    error_details['error_response'] = error_json
                    error_msg = error_json.get('message', error_json.get('error', 'Unknown error'))
                except (JSONDecodeError, ValueError):
                    # If not JSON, use text response
                    error_details['error_response'] = response.text[:MAX_ERROR_RESPONSE_LENGTH]
                    error_msg = response.text[:MAX_ERROR_MESSAGE_LENGTH] if response.text else response.reason
                
                logger.error(f"Zoho API returned {response.status_code}: {error_msg}. Details: {error_details}")
                raise Exception(f"Zoho API error ({response.status_code}): {error_msg}")
            
            data = response.json()

            if data.get('code') != 0:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Zoho API returned error code {data.get('code')}: {error_msg}")
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
