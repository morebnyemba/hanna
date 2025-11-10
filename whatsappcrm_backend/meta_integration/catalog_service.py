import os
import requests
from django.conf import settings

class MetaCatalogService:
    def __init__(self):
        self.api_version = "v18.0"
        self.whatsapp_business_account_id = os.environ.get("WHATSAPP_BUSINESS_ACCOUNT_ID")
        self.access_token = os.environ.get("META_ACCESS_TOKEN")
        self.catalog_id = os.environ.get("WHATSAPP_CATALOG_ID")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def _get_product_data(self, product):
        """
        Constructs the product data payload from a Product instance.
        """
        # Get the first image URL, if available
        first_image = product.images.first()
        image_url = first_image.image.url if first_image else None

        return {
            "name": product.name,
            "description": product.description,
            "price": str(product.price),
            "currency": product.currency,
            "sku": product.sku,
            "url": product.website_url,
            "image_url": image_url,
            "brand": product.brand,
            "country_of_origin": product.country_of_origin,
            "availability": 'in stock' if product.stock_quantity > 0 else 'out of stock',
        }

    def create_product_in_catalog(self, product):
        url = f"{self.base_url}/{self.catalog_id}/products"
        data = self._get_product_data(product)
        
        # The API expects 'retailer_id' for creation, which we map from SKU
        data['retailer_id'] = product.sku
        
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

    def update_product_in_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        data = self._get_product_data(product)
        
        response = requests.post(url, headers=self._get_headers(), json=data)
        response.raise_for_status()
        return response.json()

    def delete_product_from_catalog(self, product):
        if not product.whatsapp_catalog_id:
            raise ValueError("Product does not have a WhatsApp Catalog ID.")
        
        url = f"{self.base_url}/{product.whatsapp_catalog_id}"
        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()
        return response.json()
