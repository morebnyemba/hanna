"""
Meta Catalog Service for syncing products with Meta (Facebook) Product Catalog.

IMPORTANT: Image URL Accessibility
===================================
For products to be successfully created in Meta's catalog, the image_url URL must be:
1. Publicly accessible (no authentication required)
2. Reachable from Meta's servers (not behind a firewall/VPN)
3. Return a valid image with proper Content-Type header
4. Use HTTPS protocol (data URIs are NOT supported by Meta API)

Meta API requires the image_url field for all products (error #10801). When a product 
has no images, a static placeholder image URL is used. This ensures the product can be 
created in Meta's catalog.

CRITICAL: Meta API does NOT accept data URIs for the image_url field. The URL must be
a publicly accessible HTTP/HTTPS URL that Meta's servers can fetch.

Infrastructure Requirements for Product Images:
- Media files must be properly served by nginx or another web server
- The docker-compose.yml should include a shared volume for media files
- Nginx configuration should serve media files from the correct path
- Static files must also be served publicly for the placeholder image

Example nginx configuration:
    location /media/ {
        alias /srv/www/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
    
    location /static/ {
        alias /srv/www/static/;
        expires 7d;
        add_header Cache-Control "public";
    }

Example docker-compose volume:
    backend:
        volumes:
            - media_files:/app/mediafiles
            - static_files:/app/static
    nginx:
        volumes:
            - media_files:/srv/www/media:ro
            - static_files:/srv/www/static:ro

Django Settings:
- BACKEND_DOMAIN_FOR_CSP: Domain name for constructing absolute URLs (e.g., 'backend.hanna.co.zw')

Placeholder Image:
When a product has no images, a static placeholder image at /static/admin/img/placeholder.png
is used. This file must be served publicly via the backend domain.

If image URLs are not accessible, Meta will reject product creation with a 400 error.
"""

import requests
import logging
import json
from django.conf import settings
from .models import MetaAppConfig
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Placeholder image path for products without images
# This static file must be:
# 1. Present in the static directory (whatsappcrm_backend/static/admin/img/placeholder.png)
# 2. Publicly accessible via the backend domain (https://backend.domain.com/static/admin/img/placeholder.png)
# 3. Served by nginx or the web server (see docstring for nginx configuration)
# 
# If this file is not accessible, Meta API will reject product creation with error #10801.
# Verify accessibility by testing: curl -I https://your-backend-domain/static/admin/img/placeholder.png
#
# Meta API requires a publicly accessible URL - data URIs are NOT supported
PLACEHOLDER_IMAGE_PATH = "/static/admin/img/placeholder.png"


class MetaCatalogService:
    def __init__(self):
        try:
            active_config = MetaAppConfig.objects.get_active_config()
            self.api_version = active_config.api_version
            self.access_token = active_config.access_token
            self.catalog_id = active_config.catalog_id
        except MetaAppConfig.DoesNotExist:
            # Handle case where no active config is found
            self.api_version = "v18.0" # Default or fallback
            self.access_token = None
            self.catalog_id = None

        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _get_headers(self):
        if not self.access_token:
            raise ValueError("Meta access token is not configured.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get_product_data(self, product):
        """
        Constructs a robust product data payload from a Product instance,
        omitting fields that are null or empty to prevent '400 Bad Request' errors.
        
        Reference: https://developers.facebook.com/docs/marketing-api/catalog
        
        Required fields per Meta API:
        - retailer_id: Unique product identifier (mapped from SKU)
        - name: Product name
        - availability: in stock | out of stock | available for order
        - condition: new | refurbished | used
        - price: Price as integer in cents/minor currency units (e.g., 10000 for $100.00)
        - currency: ISO 4217 currency code (e.g., "USD")
        - link: Product URL
        - image_url: URL to product image (must be absolute URL and publicly accessible)
                    This field is required by Meta's Marketing API for product catalogs.
                    A placeholder image URL is used when the product has no images.
        
        Optional fields:
        - description: Product description
        - brand: Brand name
        - google_product_category: Google Product Category taxonomy (string or ID)
                                   e.g., 'Apparel & Accessories > Clothing > Shirts & Tops' or '212'
                                   Helps Meta categorize products for better discovery and compliance
        """
        # SKU is mandatory for the retailer_id
        if not product.sku:
            raise ValueError(f"Product '{product.name}' (ID: {product.id}) is missing an SKU, which is required for 'retailer_id'.")

        # Format price correctly - Meta expects an integer in cents (minor currency units)
        # For USD: $100.00 = 10000 cents
        price_value = 0
        if product.price is not None:
            # Convert to cents by multiplying by 100 and rounding to nearest integer
            price_value = int(round(float(product.price) * 100))

        data = {
            "retailer_id": product.sku,
            "name": product.name,
            "price": price_value,  # Integer in cents
            "currency": product.currency,
            "condition": "new",
            "availability": "in stock" if product.stock_quantity > 0 else "out of stock",
            # Provide a default link if not set, as it's often required.
            "link": product.website_url or "https://www.hanna-installations.com/product-not-available"
        }

        # Add optional description if present
        if product.description:
            data["description"] = product.description

        # Add optional brand if present
        if product.brand:
            data["brand"] = product.brand
        
        # Add optional google_product_category from the product's category if present
        # This helps Meta categorize products for better discovery and targeting
        # Accepts either category name (e.g., 'Apparel & Accessories > Clothing') or ID (e.g., '212')
        # The category mapping is defined at the ProductCategory level for consistency
        if product.category and product.category.google_product_category:
            data["google_product_category"] = product.category.google_product_category

        # Get the first image URL, if available
        # Meta API requires absolute URLs, not relative paths
        # IMPORTANT: The URL must be publicly accessible for Meta's servers to fetch
        # Meta API requires image_url field to be present
        # Error #10801: "(#10801) \"image_url\" must be specified."
        # NOTE: Data URIs are NOT supported by Meta API - must be an actual HTTP/HTTPS URL
        
        # Get the backend domain once to avoid duplication
        backend_domain = getattr(settings, 'BACKEND_DOMAIN_FOR_CSP', 'backend.hanna.co.zw')
        
        # Build placeholder URL - must be publicly accessible via HTTPS
        placeholder_url = f"https://{backend_domain}{PLACEHOLDER_IMAGE_PATH}"
        
        # IMPORTANT: Query the database directly to get fresh image data.
        # This avoids issues with Django's ORM caching the related objects on the
        # product instance. When products are created in Django admin with inline
        # images, the Product post_save signal fires BEFORE ProductImage records
        # are saved. Even when sync is triggered later by ProductImage post_save,
        # the product instance may have stale cached data in its 'images' manager.
        # By importing and querying ProductImage directly, we bypass the cache.
        from products_and_services.models import ProductImage
        first_image = ProductImage.objects.filter(product_id=product.pk).first()
        
        # Debug logging to help diagnose image detection issues
        image_count = ProductImage.objects.filter(product_id=product.pk).count()
        logger.debug(
            f"Product '{product.name}' (ID: {product.id}) has {image_count} image(s) in database. "
            f"First image object: {first_image}"
        )
        
        # Check if image exists and has a truthy URL value (not None)
        if first_image and hasattr(first_image.image, 'url') and first_image.image.url:
            # Strip whitespace and ensure string type for further validation
            image_url = str(first_image.image.url).strip()
            
            logger.debug(
                f"Product '{product.name}' (ID: {product.id}) first image URL: '{image_url}'"
            )
            
            # Validate that URL is non-empty after stripping whitespace
            if image_url:
                # If the URL is relative, convert it to absolute
                if image_url.startswith('/'):
                    # Use https as the application is behind an HTTPS proxy
                    image_url = f"https://{backend_domain}{image_url}"
                
                data["image_url"] = image_url
                logger.debug(f"Product image URL for Meta: {image_url}")
            else:
                # URL was only whitespace - use placeholder URL
                data["image_url"] = placeholder_url
                logger.warning(
                    f"Product '{product.name}' (ID: {product.id}) has image with whitespace-only URL. "
                    f"Using placeholder image URL for Meta Catalog: {placeholder_url}"
                )
        else:
            # Meta API requires image_url field even when no image is available
            # Use a static placeholder image URL - data URIs are NOT supported by Meta API
            data["image_url"] = placeholder_url
            # Enhanced debug info to help diagnose why image was not detected
            debug_info = []
            if not first_image:
                debug_info.append("no ProductImage records found")
            elif not hasattr(first_image.image, 'url'):
                debug_info.append("image field has no 'url' attribute")
            elif not first_image.image.url:
                debug_info.append(f"image.url is empty/None: '{first_image.image.url}'")
            logger.warning(
                f"Product '{product.name}' (ID: {product.id}) - {', '.join(debug_info)}. "
                f"Using placeholder image URL for Meta Catalog: {placeholder_url}"
            )

        return data

    def create_product_in_catalog(self, product):
        if not self.catalog_id:
            raise ValueError("WhatsApp Catalog ID is not configured.")
        url = f"{self.base_url}/{self.catalog_id}/products"
        data = self._get_product_data(product)
        
        logger.info(f"Creating product in Meta Catalog: {product.name} (SKU: {product.sku})")
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created product in catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_details = {}
            try:
                error_details = response.json()
                error_body = json.dumps(error_details, indent=2)
                
                # Extract useful error information
                error_message = error_details.get('error', {}).get('message', str(error_details))
                error_code = error_details.get('error', {}).get('code', response.status_code)
                error_type = error_details.get('error', {}).get('type', 'Unknown')
                
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Creation Failed\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})\n"
                    f"Error Code: {error_code}\n"
                    f"Error Type: {error_type}\n"
                    f"Error Message: {error_message}\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Full Response:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                
                # Check if the error is related to image_url
                if 'image' in error_message.lower() and 'image_url' in data:
                    logger.error(
                        f"⚠ IMAGE URL ISSUE DETECTED ⚠\n"
                        f"Image URL: {data['image_url']}\n"
                        f"This URL must be publicly accessible to Meta's servers.\n"
                        f"Test accessibility with: curl -I {data['image_url']}\n"
                        f"Ensure nginx/NPM is properly serving media files and the URL is not behind auth."
                    )
                
                # Re-raise with more context
                raise ValueError(
                    f"Meta API Error ({error_code}): {error_message}. "
                    f"Check logs for full details."
                ) from e
                
            except (ValueError, KeyError, json.JSONDecodeError):
                # If we can't parse the JSON error response
                error_body = response.text
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Creation Failed (Raw Response)\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Response Body:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                raise ValueError(
                    f"Meta API Error (HTTP {response.status_code}): {error_body[:200]}..."
                ) from e
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 30 seconds"
            logger.error(f"{error_msg} for product '{product.name}' (SKU: {product.sku})")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for product '{product.name}' (SKU: {product.sku})")
            raise ValueError(error_msg) from e

    def update_product_in_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        data = self._get_product_data(product)
        
        logger.info(f"Updating product in Meta Catalog: {product.name} (Catalog ID: {product.whatsapp_catalog_id})")
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated product in catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_details = {}
            try:
                error_details = response.json()
                error_body = json.dumps(error_details, indent=2)
                
                # Extract useful error information
                error_message = error_details.get('error', {}).get('message', str(error_details))
                error_code = error_details.get('error', {}).get('code', response.status_code)
                error_type = error_details.get('error', {}).get('type', 'Unknown')
                
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Update Failed\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, Catalog ID: {product.whatsapp_catalog_id})\n"
                    f"Error Code: {error_code}\n"
                    f"Error Type: {error_type}\n"
                    f"Error Message: {error_message}\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Full Response:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                
                # Check if the error is related to image_url
                if 'image' in error_message.lower() and 'image_url' in data:
                    logger.error(
                        f"⚠ IMAGE URL ISSUE DETECTED ⚠\n"
                        f"Image URL: {data['image_url']}\n"
                        f"This URL must be publicly accessible to Meta's servers."
                    )
                
                # Re-raise with more context
                raise ValueError(
                    f"Meta API Error ({error_code}): {error_message}. "
                    f"Check logs for full details."
                ) from e
                
            except (ValueError, KeyError, json.JSONDecodeError):
                # If we can't parse the JSON error response
                error_body = response.text
                logger.error(
                    f"═══════════════════════════════════════════════════════\n"
                    f"META API ERROR - Product Update Failed (Raw Response)\n"
                    f"═══════════════════════════════════════════════════════\n"
                    f"Product: {product.name} (ID: {product.id}, Catalog ID: {product.whatsapp_catalog_id})\n"
                    f"HTTP Status: {response.status_code}\n"
                    f"Response Body:\n{error_body}\n"
                    f"═══════════════════════════════════════════════════════"
                )
                raise ValueError(
                    f"Meta API Error (HTTP {response.status_code}): {error_body[:200]}..."
                ) from e
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 30 seconds"
            logger.error(f"{error_msg} for product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id})")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id})")
            raise ValueError(error_msg) from e

    def delete_product_from_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        
        logger.info(f"Deleting product from Meta Catalog: {product.name} (Catalog ID: {product.whatsapp_catalog_id})")
        
        response = requests.delete(url, headers=self._get_headers())
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully deleted product from catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_body = ""
            error_details = {}
            try:
                error_details = response.json()
                error_body = json.dumps(error_details, indent=2)
                logger.error(
                    f"Meta API error response when deleting product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id}):\n"
                    f"Status Code: {response.status_code}\n"
                    f"Error Details: {error_body}"
                )
            except Exception:
                error_body = response.text
                logger.error(
                    f"Meta API error response (raw) when deleting product '{product.name}' (Catalog ID: {product.whatsapp_catalog_id}):\n"
                    f"Status Code: {response.status_code}\n"
                    f"Response: {error_body}"
                )
            raise

    def set_product_visibility(self, product, visibility='published'):
        """
        Set the visibility of a product in Meta Catalog.
        
        Args:
            product: The Product instance
            visibility: 'published' (active/visible) or 'hidden' (inactive/hidden)
        
        Returns:
            dict: Response from Meta API
        
        Raises:
            ValueError: If product doesn't have a catalog ID or visibility is invalid
        """
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        if visibility not in ['published', 'hidden']:
            raise ValueError(f"Invalid visibility value: {visibility}. Must be 'published' or 'hidden'.")
        
        if not self.catalog_id:
            raise ValueError("WhatsApp Catalog ID is not configured.")
        
        url = f"{self.base_url}/{self.catalog_id}/items_batch"
        
        data = {
            "requests": [
                {
                    "method": "UPDATE",
                    "retailer_id": product.sku,
                    "data": {
                        "visibility": visibility
                    }
                }
            ]
        }
        
        logger.info(
            f"Setting product visibility in Meta Catalog: {product.name} "
            f"(SKU: {product.sku}) to '{visibility}'"
        )
        logger.debug(f"Payload: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
        
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully set product visibility. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            self._handle_batch_api_error(e, response, product, "visibility update")
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 30 seconds"
            logger.error(f"{error_msg} for product '{product.name}' visibility update")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for product '{product.name}' visibility update")
            raise ValueError(error_msg) from e

    def batch_update_products(self, updates):
        """
        Batch update multiple products in Meta Catalog.
        
        This is more efficient than individual updates when updating multiple products.
        
        Args:
            updates: List of dicts with 'product' and 'data' keys.
                     'product' is the Product instance
                     'data' is a dict of fields to update (e.g., {'visibility': 'published', 'price': 10000})
        
        Returns:
            dict: Response from Meta API with results for each product
        
        Example:
            updates = [
                {'product': product1, 'data': {'visibility': 'published'}},
                {'product': product2, 'data': {'visibility': 'hidden', 'price': 5000}},
            ]
            result = service.batch_update_products(updates)
        """
        if not self.catalog_id:
            raise ValueError("WhatsApp Catalog ID is not configured.")
        
        if not updates:
            raise ValueError("No updates provided.")
        
        # Build batch requests
        requests_list = []
        for update in updates:
            product = update.get('product')
            data = update.get('data', {})
            
            if not product:
                logger.warning("Skipping update with no product")
                continue
            
            if not product.sku:
                logger.warning(f"Skipping product '{product.name}' (ID: {product.id}) - no SKU")
                continue
            
            request_item = {
                "method": "UPDATE",
                "retailer_id": product.sku,
                "data": data
            }
            requests_list.append(request_item)
        
        if not requests_list:
            raise ValueError("No valid updates to process.")
        
        url = f"{self.base_url}/{self.catalog_id}/items_batch"
        payload = {"requests": requests_list}
        
        logger.info(f"Batch updating {len(requests_list)} products in Meta Catalog")
        logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Batch operations use a longer timeout (60s) to accommodate processing of multiple items
        response = requests.post(url, headers=self._get_headers(), json=payload, timeout=60)
        
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Batch update completed. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            self._log_and_raise_http_error(e, response, f"Batch update of {len(requests_list)} products")
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 60 seconds"
            logger.error(f"{error_msg} for batch update")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for batch update")
            raise ValueError(error_msg) from e

    def get_product_from_catalog(self, product):
        """
        Fetch product details from Meta Catalog.
        
        Args:
            product: The Product instance
        
        Returns:
            dict: Product data from Meta Catalog
        
        Raises:
            ValueError: If product doesn't have a catalog ID
        """
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        
        # Request common fields
        params = {
            "fields": "id,retailer_id,name,price,currency,availability,visibility,image_url,url,description,brand"
        }
        
        logger.info(f"Fetching product from Meta Catalog: {product.name} (Catalog ID: {product.whatsapp_catalog_id})")
        
        response = requests.get(url, headers=self._get_headers(), params=params, timeout=30)
        
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully fetched product from catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            self._log_and_raise_http_error(e, response, f"Fetch product '{product.name}'")
        except requests.exceptions.Timeout:
            error_msg = "Request to Meta API timed out after 30 seconds"
            logger.error(f"{error_msg} for product '{product.name}'")
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error connecting to Meta API: {str(e)}"
            logger.error(f"{error_msg} for product '{product.name}'")
            raise ValueError(error_msg) from e

    def sync_product_update(self, product):
        """
        Sync product updates to Meta Catalog. This is a convenience method that:
        1. Creates the product if it doesn't exist in Meta Catalog
        2. Updates the product if it already exists
        
        Args:
            product: The Product instance
        
        Returns:
            dict: Response from Meta API
        """
        if product.whatsapp_catalog_id:
            return self.update_product_in_catalog(product)
        else:
            return self.create_product_in_catalog(product)

    def _log_and_raise_http_error(self, exception, response, operation_desc):
        """
        Shared helper to log and raise HTTP errors from Meta API.
        
        Args:
            exception: The original HTTPError exception
            response: The HTTP response object
            operation_desc: Human-readable description of the operation (e.g., "Batch update of 5 products")
        
        Raises:
            ValueError: Always raises with formatted error message
        """
        try:
            error_details = response.json()
            error_body = json.dumps(error_details, indent=2)
            error_message = error_details.get('error', {}).get('message', str(error_details))
            error_code = error_details.get('error', {}).get('code', response.status_code)
            
            logger.error(
                f"═══════════════════════════════════════════════════════\n"
                f"META API ERROR - {operation_desc} Failed\n"
                f"═══════════════════════════════════════════════════════\n"
                f"Error Code: {error_code}\n"
                f"Error Message: {error_message}\n"
                f"HTTP Status: {response.status_code}\n"
                f"Full Response:\n{error_body}\n"
                f"═══════════════════════════════════════════════════════"
            )
            
            raise ValueError(
                f"Meta API Error ({error_code}): {error_message}"
            ) from exception
            
        except (json.JSONDecodeError, KeyError, TypeError):
            error_body = response.text
            logger.error(
                f"Meta API error (raw) for '{operation_desc}': "
                f"HTTP {response.status_code}\n{error_body}"
            )
            raise ValueError(
                f"Meta API Error (HTTP {response.status_code}): {error_body[:200]}..."
            ) from exception

    def _handle_batch_api_error(self, exception, response, product, operation):
        """
        Handle errors from batch API operations.
        
        Args:
            exception: The original exception
            response: The HTTP response object
            product: The Product instance
            operation: Description of the operation (e.g., "visibility update")
        """
        try:
            error_details = response.json()
            error_body = json.dumps(error_details, indent=2)
            error_message = error_details.get('error', {}).get('message', str(error_details))
            error_code = error_details.get('error', {}).get('code', response.status_code)
            
            logger.error(
                f"═══════════════════════════════════════════════════════\n"
                f"META API ERROR - {operation.title()} Failed\n"
                f"═══════════════════════════════════════════════════════\n"
                f"Product: {product.name} (ID: {product.id}, SKU: {product.sku})\n"
                f"Error Code: {error_code}\n"
                f"Error Message: {error_message}\n"
                f"HTTP Status: {response.status_code}\n"
                f"Full Response:\n{error_body}\n"
                f"═══════════════════════════════════════════════════════"
            )
            
            raise ValueError(
                f"Meta API Error ({error_code}): {error_message}. "
                f"Check logs for full details."
            ) from exception
            
        except (ValueError, KeyError, json.JSONDecodeError):
            error_body = response.text
            logger.error(
                f"Meta API {operation} error (raw) for '{product.name}': "
                f"HTTP {response.status_code}\n{error_body}"
            )
            raise ValueError(
                f"Meta API Error (HTTP {response.status_code}): {error_body[:200]}..."
            ) from exception
