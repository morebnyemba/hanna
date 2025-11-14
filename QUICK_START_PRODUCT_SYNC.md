# Quick Start Guide - Product Sync Fix

## What Was Fixed

✅ **Price Format Error** - Meta API now receives prices as integer cents (e.g., 10000 for $100.00)  
✅ **Media Files Configuration** - Added shared volume for media files across all backend services  
✅ **Production Media Serving** - Configured Django to serve media files in production mode  
✅ **Enhanced Error Logging** - Full Meta API error responses now logged for debugging  

## Immediate Next Steps

### 1. Restart Services
```bash
cd /home/runner/work/hanna/hanna
docker-compose down
docker-compose up -d
```

This will:
- Create the new `mediafiles_volume`
- Mount it in all backend services
- Apply the code changes

### 2. Test Product Sync

**Via Django Admin:**
1. Navigate to `/admin/products_and_services/product/`
2. Create or edit a product with:
   - ✅ Name: "Test Product"
   - ✅ SKU: Must be unique (e.g., "TEST-001")
   - ✅ Price: Any valid price (e.g., 100.00)
   - ✅ Currency: USD
   - ✅ Is Active: Checked ✓
   - ✅ Image: Upload a product image
   - ✅ Brand: Add a brand name
3. Click "Save"

**Check Logs:**
```bash
docker logs whatsappcrm_backend_app --tail=50 | grep -i catalog
```

**Expected Success Log:**
```
[INFO] catalog_service Creating product in Meta Catalog: Test Product (SKU: TEST-001)
[DEBUG] catalog_service Payload: {'retailer_id': 'TEST-001', 'name': 'Test Product', 'price': 10000, ...}
[INFO] signals Successfully created product in Meta Catalog. Catalog ID: [catalog_id]
```

### 3. Verify in Meta Business Manager

1. Go to [Meta Business Manager](https://business.facebook.com/)
2. Navigate to **Catalog Manager**
3. Find your catalog (ID from settings: `catalog_id`)
4. Verify the product appears with correct:
   - Name
   - Price (displayed as $100.00)
   - Image (should be visible)
   - Description

### 4. Verify Image Accessibility

Test that product images are publicly accessible:

```bash
# Replace with actual image URL from your product
curl -I https://backend.hanna.co.zw/media/product_images/your-image.png
```

**Expected Response:**
```
HTTP/2 200
content-type: image/png
content-length: [size]
```

## Troubleshooting

### Problem: Still Getting Price Error

**Check:** Is the price field populated?
```python
# In Django admin or shell
from products_and_services.models import Product
product = Product.objects.get(sku='TEST-001')
print(f"Price: {product.price}, Type: {type(product.price)}")
```

**Solution:** Ensure price is set and is a valid decimal number.

### Problem: Image Not Loading

**Check 1:** Is the image uploaded?
```bash
docker exec whatsappcrm_backend_app ls -la /app/mediafiles/product_images/
```

**Check 2:** Can you access it via browser?
```
https://backend.hanna.co.zw/media/product_images/[image-name]
```

**Solution:** 
- If 404: Image not uploaded properly
- If 403: Check file permissions
- If timeout: Check NPM configuration

### Problem: Product Not Syncing

**Check 1:** Is the product active and has SKU?
```python
from products_and_services.models import Product
product = Product.objects.get(id=YOUR_PRODUCT_ID)
print(f"Active: {product.is_active}, SKU: {product.sku}")
```

**Check 2:** Are signals registered?
```bash
docker logs whatsappcrm_backend_app --tail=100 | grep "ProductsAndServicesConfig"
```

Should see: `[INFO] apps ProductsAndServicesConfig ready.`

**Check 3:** View detailed error logs:
```bash
docker logs whatsappcrm_backend_app --tail=200 | grep -A 10 "ERROR.*catalog\|ERROR.*signals"
```

## Key Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `catalog_service.py` | Price → integer cents | Fix Meta API compatibility |
| `docker-compose.yml` | Added mediafiles_volume | Share media files across services |
| `urls.py` | Serve media in production | Enable image access via NPM |

## Documentation

- **Detailed Setup Guide**: `MEDIA_FILES_CONFIGURATION.md`
- **Complete Fix Summary**: `PRODUCT_SYNC_FIX_SUMMARY.md`
- **This Quick Start**: `QUICK_START_PRODUCT_SYNC.md`

## Common Questions

**Q: Do I need to update existing products?**  
A: No. When you edit any existing product and save it, the signal will automatically sync it with the new price format.

**Q: Will this fix work for all currencies?**  
A: Yes. The conversion to cents (minor currency units) works for all decimal-based currencies. For currencies without decimal places (like JPY), the price is already in minor units.

**Q: What if Meta API still returns errors?**  
A: Check the logs for the full error response. Common issues:
- Image URL not accessible from internet
- Missing required fields (SKU, price, name)
- Invalid brand or description characters
- Catalog ID not configured in Meta settings

**Q: Can I test without affecting production catalog?**  
A: Yes. In Meta Business Manager, you can create a test catalog and update the `catalog_id` in Django admin → Meta Integration → Meta App Config to point to the test catalog.

## Support

If you encounter issues after deployment:

1. Check logs: `docker logs whatsappcrm_backend_app --tail=100`
2. Verify configuration: Django Admin → Meta Integration → Meta App Config
3. Test image accessibility: `curl -I [image-url]`
4. Review documentation: `MEDIA_FILES_CONFIGURATION.md`

## Success Indicators

✅ Products show in Meta Catalog Manager  
✅ Prices display correctly (e.g., $100.00)  
✅ Images are visible in catalog  
✅ No 400 errors in logs  
✅ Products can be shared via WhatsApp  

---

**Last Updated:** 2025-11-14  
**Issue:** Product Sync with Meta Catalog is Failing  
**Status:** ✅ RESOLVED
