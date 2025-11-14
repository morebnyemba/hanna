# Meta Product Catalog Sync - Documentation

## Overview

Products in the `products_and_services` app are automatically synchronized with Meta (Facebook/WhatsApp) Product Catalog using Django signals. When a product is created, updated, or deleted, the changes are propagated to Meta's API.

## How It Works

### Signal Handlers

The `signals.py` file contains three main signal handlers:

1. **`sync_product_to_meta_catalog`** (post_save): Handles product creation and updates
2. **`delete_product_from_meta_catalog`** (post_delete): Handles product deletion

### Sync Requirements

For a product to be synced to Meta Catalog, it must meet these criteria:

- ✅ Have a valid SKU (required as `retailer_id` in Meta API)
- ✅ Be marked as active (`is_active=True`)
- ✅ Not have exceeded max sync attempts (5 attempts)
- ✅ Not be in exponential backoff period after a failure

### Retry Logic with Exponential Backoff

If a sync fails, the system implements intelligent retry logic:

1. **First attempt**: Immediate (on save)
2. **Second attempt**: After 5 minutes
3. **Third attempt**: After 15 minutes (cumulative: 20 min)
4. **Fourth attempt**: After 45 minutes (cumulative: 1hr 5min)
5. **Fifth attempt**: After 2.25 hours (cumulative: 3hr 20min)
6. **After 5 attempts**: System stops trying automatically

### Tracking Fields

Each Product model has these tracking fields:

- `meta_sync_attempts`: Number of sync attempts (0-5)
- `meta_sync_last_error`: Last error message from Meta API
- `meta_sync_last_attempt`: Timestamp of last attempt
- `meta_sync_last_success`: Timestamp of last successful sync
- `whatsapp_catalog_id`: Meta's catalog ID (set on successful creation)

## Admin Interface

### Sync Status Column

The admin list view shows color-coded sync status:

- 🟢 **✓ Synced**: Product successfully synced to Meta
- 🟠 **⚠ Retry pending (N/5)**: Failed but will retry automatically
- 🔴 **✗ Failed (max attempts)**: Exceeded 5 attempts, needs manual intervention
- ⚪ **○ Not synced**: New product, not yet synced

### Admin Actions

**Reset Meta sync attempts**
- Select products with failed sync
- Choose "Reset Meta sync attempts" from Actions dropdown
- Click "Go"
- Products will be retried on next save

### Viewing Sync Details

1. Go to Product detail page in admin
2. Expand "Meta Catalog Sync Status" section
3. View:
   - Number of sync attempts
   - Last error message (if any)
   - Last attempt timestamp
   - Last successful sync timestamp

## Troubleshooting

### Common Issues

#### 1. Image URL Not Accessible

**Error**: `image_link` errors from Meta API

**Cause**: Meta's servers cannot fetch the product image

**Default Behavior**: Images are DISABLED by default to prevent sync failures

**Solution Option 1 - Keep Images Disabled (Recommended)**:
```python
# In Django settings (default):
META_CATALOG_INCLUDE_IMAGES = False  # Images will not be sent to Meta

# Products will sync without images, which is acceptable for Meta Catalog
# This prevents sync failures when images aren't publicly accessible
```

**Solution Option 2 - Enable Images After Fixing Accessibility**:
```bash
# 1. Test if image URL is publicly accessible
curl -I https://backend.hanna.co.zw/media/product_images/example.png

# Should return: HTTP/2 200
# If not, check:
# 1. Nginx is serving media files
# 2. Media files volume is mounted correctly in docker-compose
# 3. URL is not behind authentication

# 2. After fixing, enable in Django settings:
# META_CATALOG_INCLUDE_IMAGES = True
```

**Docker Configuration**:
```yaml
# docker-compose.yml
backend:
  volumes:
    - mediafiles_volume:/app/mediafiles

nginx:
  volumes:
    - mediafiles_volume:/srv/www/media:ro
```

**Nginx Configuration**:
```nginx
# nginx.conf
location /media/ {
    alias /srv/www/media/;
    expires 7d;
    add_header Cache-Control "public";
}
```

#### 2. Product Has No SKU

**Error**: `Product '...' has no SKU. Skipping Meta Catalog sync.`

**Solution**: Add a unique SKU to the product before saving.

#### 3. Configuration Not Set

**Error**: `WhatsApp Catalog ID is not configured.`

**Solution**: 
1. Go to Meta Integration admin
2. Set an active MetaAppConfig
3. Ensure `catalog_id` is configured

#### 4. Max Attempts Exceeded

**Error**: Product shows "Failed (max attempts)" in admin

**Solution**:
1. Fix the underlying issue (e.g., image URL, configuration)
2. Select the product in admin
3. Use "Reset Meta sync attempts" action
4. Save the product to retry

#### 5. Network Timeout

**Error**: `Request to Meta API timed out after 30 seconds`

**Solution**: Check network connectivity and Meta API status

### Viewing Detailed Error Logs

Errors are logged with prominent formatting:

```bash
# View Django logs (adjust path to your setup)
docker logs whatsappcrm_backend_app | grep "META API ERROR"

# Look for bordered error messages like:
═══════════════════════════════════════════════════════
META API ERROR - Product Creation Failed
═══════════════════════════════════════════════════════
Product: MUST 3kva Inverter (ID: 5, SKU: MUST-3KVA)
Error Code: 100
Error Type: OAuthException
Error Message: Invalid OAuth access token
...
```

## Manual Sync Retry

### Via Admin Interface

1. Navigate to Products in Django Admin
2. Find the product with sync failure
3. Check the error in "Meta Catalog Sync Status" section
4. Fix the underlying issue
5. Use "Reset Meta sync attempts" action
6. Save the product (this triggers sync)

### Via Django Shell

```python
from products_and_services.models import Product

# Reset a specific product
product = Product.objects.get(id=5)
product.reset_meta_sync_attempts()
product.save()  # This will trigger sync

# Reset all failed products
failed_products = Product.objects.filter(meta_sync_attempts__gte=5)
for product in failed_products:
    product.reset_meta_sync_attempts()
    product.save()
```

### Via Management Command (Create if Needed)

```python
# Create: products_and_services/management/commands/retry_meta_sync.py
from django.core.management.base import BaseCommand
from products_and_services.models import Product

class Command(BaseCommand):
    help = 'Retry Meta Catalog sync for failed products'

    def handle(self, *args, **options):
        failed_products = Product.objects.filter(
            meta_sync_attempts__gte=5,
            is_active=True
        ).exclude(sku__isnull=True)
        
        self.stdout.write(f"Found {failed_products.count()} products to retry")
        
        for product in failed_products:
            product.reset_meta_sync_attempts()
            product.save()
            self.stdout.write(f"  ✓ Retrying: {product.name}")
        
        self.stdout.write(self.style.SUCCESS('Done!'))
```

## API Payload Structure

Products are sent to Meta with this payload:

```json
{
  "retailer_id": "PRODUCT-SKU-001",
  "name": "Product Name",
  "price": 10000,  // in cents (100.00 USD)
  "currency": "USD",
  "condition": "new",
  "availability": "in stock",  // or "out of stock"
  "link": "https://example.com/product-page",
  "description": "Product description (optional)",
  "brand": "Brand Name (optional)",
  "image_link": "https://backend.hanna.co.zw/media/product_images/image.png"
}
```

### Field Mappings

| Django Model Field | Meta API Field | Required | Notes |
|-------------------|----------------|----------|-------|
| `sku` | `retailer_id` | Yes | Unique identifier |
| `name` | `name` | Yes | Product name |
| `price` | `price` | Yes | Integer in cents |
| `currency` | `currency` | Yes | ISO 4217 code |
| `stock_quantity` | `availability` | Yes | Maps to "in stock" or "out of stock" |
| `website_url` | `link` | Yes | Falls back to default URL |
| `description` | `description` | No | Optional |
| `brand` | `brand` | No | Optional |
| `images[0].image.url` | `image_link` | No | Must be publicly accessible |

## Meta API Documentation

Official Meta documentation:
- Product Catalog API: https://developers.facebook.com/docs/marketing-api/catalog
- WhatsApp Business API: https://developers.facebook.com/docs/whatsapp/business-management-api

## Preventing Infinite Loops

The signal handler has multiple safeguards to prevent infinite loops:

1. **Thread-local storage**: Prevents recursive signal calls within the same thread
2. **update_fields check**: Ignores saves that only update sync tracking fields
3. **Query update vs save**: Uses `Product.objects.filter().update()` to avoid triggering signals when updating tracking fields

## Best Practices

### Before Creating Products

1. ✅ Ensure Meta integration is configured
2. ✅ Verify media files are accessible via nginx
3. ✅ Add product images before saving (if available)
4. ✅ Include all required fields (SKU, name, price)

### Monitoring

1. Check admin "Meta Sync Status" column regularly
2. Set up alerts for products with `meta_sync_attempts >= 3`
3. Review error logs for patterns (e.g., all image errors)

### Bulk Operations

When importing many products:

```python
# Disable signals temporarily for bulk operations
from django.db.models.signals import post_save
from products_and_services.signals import sync_product_to_meta_catalog
from products_and_services.models import Product

# Disconnect signal
post_save.disconnect(sync_product_to_meta_catalog, sender=Product)

# Do bulk operations
Product.objects.bulk_create([...])

# Reconnect signal
post_save.connect(sync_product_to_meta_catalog, sender=Product)

# Manually trigger sync for new products
for product in Product.objects.filter(whatsapp_catalog_id__isnull=True):
    product.save()  # This will trigger sync
```

## Support

For issues not covered here:

1. Check Django logs for detailed error messages
2. Verify Meta API status: https://developers.facebook.com/status/
3. Test API credentials in Meta Business Suite
4. Review Meta's API changelog for breaking changes
