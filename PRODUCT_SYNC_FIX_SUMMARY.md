# Product Sync with Meta Catalog - Fix Summary

## Issue Description

Products were failing to sync with Meta (Facebook) Product Catalog when created or updated through the Django admin or API. The error logs showed:

```
[2025-11-14 17:48:25] ERROR catalog_service Meta API error response for product 'MUST 3kva Inverter' (SKU: 5784935):
Status Code: 400
Error Details: {
  "error": {
    "message": "(#100) Param price must be an integer",
    "type": "OAuthException",
    "code": 100,
    "fbtrace_id": "ANwiRpA8VHaqfxsg9-e-yS5"
  }
}
```

## Root Causes Identified

### 1. Price Format Error (Critical)
**Problem**: The catalog service was sending price as a decimal string (e.g., "100.00"), but Meta's API expects price as an integer in cents/minor currency units (e.g., 10000 for $100.00).

**Solution**: Updated `_get_product_data()` in `catalog_service.py` to convert price to integer cents:

```python
# Before:
price_value = "0.00"
if product.price is not None:
    price_value = f"{float(product.price):.2f}"

# After:
price_value = 0
if product.price is not None:
    price_value = int(round(float(product.price) * 100))
```

### 2. Media Files Not Accessible (Infrastructure)
**Problem**: Product images were stored in the backend's mediafiles directory, but there was no shared volume configuration in docker-compose.yml, potentially causing issues with file access across services.

**Solution**: Added `mediafiles_volume` to docker-compose.yml and mounted it in all backend-related services:
- backend
- celery_io_worker
- celery_cpu_worker
- celery_beat
- email_idle_fetcher

### 3. Media Files Not Served in Production
**Problem**: Django's default configuration only serves media files when DEBUG=True. In production, media requests were not being handled properly.

**Solution**: Updated `urls.py` to serve media files regardless of DEBUG setting, since Nginx Proxy Manager proxies all requests to Django anyway.

## Changes Made

### 1. `whatsappcrm_backend/meta_integration/catalog_service.py`

**Price conversion fix**:
- Line 93-96: Changed price from decimal string to integer cents
- Line 75: Updated docstring to reflect correct price format

**Enhanced error logging**:
- Lines 156-190: Added detailed error logging for create operations
- Lines 204-238: Added detailed error logging for update operations
- Lines 256-275: Added detailed error logging for delete operations
- Now logs full Meta API error responses including error code, message, and trace ID

**Image URL construction**:
- Lines 121-140: Added logic to construct absolute image URLs for Meta
- Added debug logging for image URLs
- Added warning for products without images

### 2. `docker-compose.yml`

**Added mediafiles volume**:
- Line 136: Declared `mediafiles_volume` in volumes section
- Lines 33, 67, 81, 94, 107: Mounted volume in all backend services

### 3. `whatsappcrm_backend/whatsappcrm_backend/urls.py`

**Media serving configuration**:
- Lines 69-74: Changed media file serving to work in production mode
- Updated comments to explain the NPM proxy configuration

### 4. Documentation

**Created `MEDIA_FILES_CONFIGURATION.md`**:
- Complete guide to media file configuration
- NPM (Nginx Proxy Manager) setup instructions
- Troubleshooting guide
- Meta Catalog requirements
- Testing procedures
- Future improvement recommendations

## Testing & Verification

### Price Conversion Testing
Created and ran comprehensive price conversion tests:
- ✅ Basic decimal prices ($100.00 → 10000)
- ✅ Prices with cents ($100.50 → 10050)
- ✅ Sub-dollar amounts ($0.99 → 99)
- ✅ Rounding behavior (100.999 → 10100)
- ✅ Edge cases (None, 0, very small amounts)

All tests passed successfully.

### Syntax Validation
- ✅ Python syntax check passed on all modified files
- ✅ No import errors
- ✅ Existing unit tests structure verified

## Infinite Loop Investigation

The user expressed concern about potential infinite loops based on log entries showing repeated "Status Update" and "Webhook POST" messages.

### Findings:
1. **No catalog webhook handlers**: The webhook handler in `meta_integration/views.py` only handles:
   - Message status updates (sent, delivered, read, failed)
   - Template status updates
   - Account updates
   - Error notifications
   
   There are NO handlers for catalog/product-related webhooks.

2. **Robust signal protection**: The `post_save` signal handler in `products_and_services/signals.py` has multiple safeguards:
   - Thread-local processing flags to prevent recursive calls
   - Update fields checking to skip sync when only catalog_id is updated
   - Uses `.update()` instead of `.save()` when updating catalog_id

3. **Log entries explained**: The repeated log entries are for message status updates (normal WhatsApp message delivery confirmations), not product syncing.

**Conclusion**: ✅ No infinite loop risk exists in the product sync implementation.

## Meta Catalog API Requirements

For successful product synchronization:

### Required Fields
- `retailer_id`: Unique product identifier (mapped from SKU) ✅
- `name`: Product name ✅
- `price`: **Integer in cents** (e.g., 10000 for $100.00) ✅
- `currency`: ISO 4217 currency code (e.g., "USD") ✅
- `condition`: "new", "refurbished", or "used" ✅
- `availability`: "in stock" or "out of stock" ✅
- `link`: Product URL ✅

### Optional Fields
- `description`: Product description ✅
- `brand`: Brand name ✅
- `image_link`: Absolute URL to product image (must be publicly accessible) ✅

### Image Requirements
- **Protocol**: Must use HTTPS
- **Authentication**: Publicly accessible (no auth required)
- **Content-Type**: Proper image MIME type
- **Accessibility**: Reachable from Meta's servers
- **Format**: JPEG or PNG recommended
- **Size**: Max 8MB recommended

## Deployment Instructions

1. **Apply docker-compose changes**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
   This will create the new `mediafiles_volume` and mount it in all services.

2. **Verify media file access**:
   ```bash
   # Test a product image URL
   curl -I https://backend.hanna.co.zw/media/product_images/[image_name].png
   ```
   Should return HTTP 200 with Content-Type: image/png

3. **Test product sync**:
   - Create or update a product via Django admin
   - Check logs for successful sync
   - Verify product appears in Meta Business Manager → Catalog

4. **Monitor for errors**:
   ```bash
   docker logs whatsappcrm_backend_app | grep -i "catalog_service\|signals"
   ```

## Future Improvements

### Performance Optimization
1. **Use a CDN**: Store media files on a CDN (AWS CloudFront, Cloudflare) for better global performance
2. **Object Storage**: Use S3-compatible storage (AWS S3, MinIO, DigitalOcean Spaces)
3. **Django-storages**: Configure django-storages to automatically upload media to cloud storage
4. **NPM Direct Serving**: Configure Nginx Proxy Manager to serve media files directly from volume

### Monitoring & Alerting
1. Add Prometheus metrics for product sync success/failure rates
2. Set up alerts for repeated sync failures
3. Create dashboard to monitor catalog sync health

### Error Handling
1. Implement retry logic with exponential backoff for transient failures
2. Add dead-letter queue for failed syncs
3. Create admin notification system for critical sync failures

## Related Files

- `whatsappcrm_backend/meta_integration/catalog_service.py`: Meta Catalog API integration
- `whatsappcrm_backend/products_and_services/signals.py`: Signal handlers for product sync
- `whatsappcrm_backend/products_and_services/models.py`: Product model definition
- `whatsappcrm_backend/products_and_services/apps.py`: App configuration with signal registration
- `whatsappcrm_backend/whatsappcrm_backend/urls.py`: URL configuration
- `docker-compose.yml`: Docker orchestration
- `MEDIA_FILES_CONFIGURATION.md`: Detailed media configuration guide

## References

- [Meta Marketing API - Product Catalog](https://developers.facebook.com/docs/marketing-api/catalog)
- [WhatsApp Business API - Catalog](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/sell-products-and-services)
- [Django Media Files Documentation](https://docs.djangoproject.com/en/stable/topics/files/)

## Issue Status

✅ **RESOLVED** - All identified issues have been fixed:
- ✅ Price format corrected to integer cents
- ✅ Media files volume configuration added
- ✅ Media serving configured for production
- ✅ Enhanced error logging implemented
- ✅ Comprehensive documentation created
- ✅ No infinite loop risk confirmed

The product sync should now work correctly. Products with valid SKUs, images, and prices will automatically sync to Meta Catalog when created or updated.
