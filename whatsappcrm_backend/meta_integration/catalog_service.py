import requests
import logging
from django.conf import settings
from .models import MetaAppConfig
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
        - price: Price as string with decimal (e.g., "100.00")
        - currency: ISO 4217 currency code (e.g., "USD")
        - link: Product URL
        
        Optional fields:
        - description: Product description
        - brand: Brand name
        - image_link: URL to product image (must be absolute URL and publicly accessible)
        """
        # SKU is mandatory for the retailer_id
        if not product.sku:
            raise ValueError(f"Product '{product.name}' (ID: {product.id}) is missing an SKU, which is required for 'retailer_id'.")

        # Format price correctly - Meta expects a string with 2 decimal places
        price_value = "0.00"
        if product.price is not None:
            price_value = f"{float(product.price):.2f}"

        data = {
            "retailer_id": product.sku,
            "name": product.name,
            "price": price_value,
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

        # Get the first image URL, if available
        # Meta API requires absolute URLs, not relative paths
        # IMPORTANT: The URL must be publicly accessible for Meta's servers to fetch
        first_image = product.images.first()
        if first_image and hasattr(first_image.image, 'url'):
            image_url = first_image.image.url
            # If the URL is relative, convert it to absolute
            if image_url.startswith('/'):
                # Get the backend domain from settings
                backend_domain = getattr(settings, 'BACKEND_DOMAIN_FOR_CSP', 'backend.hanna.co.zw')
                # Use https as the application is behind an HTTPS proxy
                image_url = f"https://{backend_domain}{image_url}"
            data["image_link"] = image_url
            logger.debug(f"Product image URL for Meta: {image_url}")

        return data

    def create_product_in_catalog(self, product):
        if not self.catalog_id:
            raise ValueError("WhatsApp Catalog ID is not configured.")
        url = f"{self.base_url}/{self.catalog_id}/products"
        data = self._get_product_data(product)
        
        logger.info(f"Creating product in Meta Catalog: {product.name} (SKU: {product.sku})")
        logger.debug(f"Payload: {data}")
        
        response = requests.post(url, headers=self._get_headers(), json=data)
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully created product in catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_body = ""
            try:
                error_body = response.json()
                logger.error(f"Meta API error response: {error_body}")
            except Exception:
                error_body = response.text
                logger.error(f"Meta API error response (raw): {error_body}")
            raise

    def update_product_in_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        data = self._get_product_data(product)
        
        logger.info(f"Updating product in Meta Catalog: {product.name} (Catalog ID: {product.whatsapp_catalog_id})")
        logger.debug(f"Payload: {data}")
        
        response = requests.post(url, headers=self._get_headers(), json=data)
        
        # Log the full response for debugging
        try:
            response.raise_for_status()
            result = response.json()
            logger.info(f"Successfully updated product in catalog. Response: {result}")
            return result
        except requests.exceptions.HTTPError as e:
            # Log the full error response from Meta
            error_body = ""
            try:
                error_body = response.json()
                logger.error(f"Meta API error response: {error_body}")
            except Exception:
                error_body = response.text
                logger.error(f"Meta API error response (raw): {error_body}")
            raise

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
            try:
                error_body = response.json()
                logger.error(f"Meta API error response: {error_body}")
            except Exception:
                error_body = response.text
                logger.error(f"Meta API error response (raw): {error_body}")
            raise
