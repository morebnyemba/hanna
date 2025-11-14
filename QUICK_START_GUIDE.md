# Quick Start Guide - Product Sync Fix

## 🎯 What This Fix Does

Your product sync with Meta (WhatsApp) Catalog now has:
- ✅ **Smart retry** with exponential backoff
- ✅ **Error tracking** in database
- ✅ **Admin visibility** with color-coded status
- ✅ **Detailed logging** for easy diagnosis

## 🚀 Deployment (5 minutes)

### Step 1: Apply Database Changes
```bash
# Migration will be handled separately in production
# Ensure these fields are added to products_and_services.Product table:
# - meta_sync_attempts (integer, default 0)
# - meta_sync_last_error (text, nullable)
# - meta_sync_last_attempt (timestamp, nullable)
# - meta_sync_last_success (timestamp, nullable)
```

### Step 2: Enable Image Sync (Optional)
```bash
# Add to your Django settings if images are publicly accessible:
# META_CATALOG_INCLUDE_IMAGES = True
# 
# Leave disabled (default False) if images are not publicly accessible
# Products will sync without images, which is acceptable for Meta Catalog
```

### Step 3: Restart Services
```bash
docker-compose restart backend
```

### Step 4: Verify in Admin
1. Go to **Django Admin → Products**
2. Look for new **"Meta Sync Status"** column
3. Should see color-coded status indicators

## 📊 Understanding Sync Status

In the admin list view, you'll see one of these statuses:

| Icon | Status | Meaning | Action Needed |
|------|--------|---------|---------------|
| 🟢 | **✓ Synced** | Product successfully synced to Meta | None - working! |
| 🟠 | **⚠ Retry pending (2/5)** | Failed but will retry automatically | Wait or check error details |
| 🔴 | **✗ Failed (max attempts)** | Exceeded 5 attempts, stopped | Fix issue + manual reset |
| ⚪ | **○ Not synced** | New product, not yet attempted | Will sync on next save |

## 🔧 Fixing Failed Products

### If you see 🔴 **✗ Failed (max attempts)**:

**Step 1: View the Error**
1. Click on the product
2. Expand **"Meta Catalog Sync Status"** section
3. Read the error in **"Last Meta Sync Error"** field

**Step 2: Fix the Issue**

Common issues and fixes:

| Error | Fix |
|-------|-----|
| Image URL not accessible | Check nginx config, verify image exists |
| No SKU | Add a unique SKU to the product |
| No catalog ID configured | Set up Meta App Config |
| Invalid OAuth token | Update access token in Meta App Config |

**Step 3: Reset and Retry**
1. Select the product(s) in admin list
2. Choose **"Reset Meta sync attempts"** from Actions
3. Click **"Go"**
4. Save the product

**Step 4: Verify Success**
- Status should change to 🟢 **✓ Synced**
- Check logs: `docker-compose logs backend | grep "✓ Successfully"`

## 🔍 Monitoring

### Watch Real-Time Logs
```bash
# See all sync activity
docker-compose logs -f backend | grep signals

# See errors only
docker-compose logs -f backend | grep "META API ERROR"

# See successful syncs
docker-compose logs -f backend | grep "✓ Successfully"
```

### What Good Logs Look Like
```
[INFO] signals Creating new product in Meta Catalog: 'Product X' - Attempt 1/5
[INFO] signals ✓ Successfully created product in Meta Catalog. Catalog ID: 12345
```

### What Bad Logs Look Like
```
═══════════════════════════════════════════════════════
META API ERROR - Product Creation Failed
═══════════════════════════════════════════════════════
Product: Product X (ID: 5, SKU: ABC-123)
Error Code: 100
Error Type: OAuthException
Error Message: [Details here]
═══════════════════════════════════════════════════════
```

## 📋 Common Scenarios

### Scenario 1: Images Not Publicly Accessible

**Problem**: Image URLs are not accessible to Meta's servers

**Solution Option 1 - Disable Image Sync (Recommended)**:
```python
# In your Django settings, keep images disabled (default):
# META_CATALOG_INCLUDE_IMAGES = False  (default)
# 
# Products will sync WITHOUT images, which is acceptable for Meta Catalog
# The catalog will show product info without images until this is fixed
```

**Solution Option 2 - Fix Image Accessibility**:
```bash
# 1. Test an image URL
curl -I https://backend.hanna.co.zw/media/product_images/test.png

# Should return: HTTP/2 200
# If 404/403, you need to:
# 1. Configure nginx to serve media files publicly
# 2. Update docker-compose.yml to share media volume with nginx
# 3. Ensure no authentication is required for /media/ URLs

# 2. After fixing, enable in settings:
# META_CATALOG_INCLUDE_IMAGES = True
```

**Note**: By default, image sync is DISABLED to prevent sync failures when images aren't accessible.

### Scenario 2: Products Without SKU Not Syncing

**Problem**: SKU is required by Meta API

**Solution**:
1. Filter products: `Product.objects.filter(sku__isnull=True)`
2. Add SKUs to all products
3. Save to trigger sync

### Scenario 3: Need to Bulk Retry Many Products

**Solution**:
```python
# Django shell
from products_and_services.models import Product

# Get all failed products
failed = Product.objects.filter(meta_sync_attempts__gte=5)
print(f"Found {failed.count()} failed products")

# Reset and save
for product in failed:
    product.reset_meta_sync_attempts()
    product.save()
    print(f"Retrying: {product.name}")
```

Or use admin bulk action:
1. Filter by "Meta Sync Status" = Failed
2. Select all
3. Actions → "Reset Meta sync attempts"
4. Go
5. Select all again
6. Save (use bulk edit if needed)

### Scenario 4: Product Keeps Failing

**If a product fails 5 times**, it stops retrying to prevent API abuse.

**Check these things**:
1. ✅ Product has SKU
2. ✅ Product is active (`is_active=True`)
3. ✅ Meta App Config is set up correctly
4. ✅ Image URL is publicly accessible (if product has images)
5. ✅ Access token is valid
6. ✅ Catalog ID is correct

**Test Meta API manually**:
```bash
# Get your access token from Meta App Config
TOKEN="your_token_here"
CATALOG_ID="your_catalog_id"

# Try creating a simple product
curl -X POST "https://graph.facebook.com/v18.0/${CATALOG_ID}/products" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "retailer_id": "TEST-001",
    "name": "Test Product",
    "price": 10000,
    "currency": "USD",
    "condition": "new",
    "availability": "in stock",
    "link": "https://example.com"
  }'
```

## 🎓 Understanding Retry Timing

When a product fails, it retries with increasing delays:

```
Attempt 1: Immediate (on save)      ← You click Save
    ↓
  FAILED
    ↓
    Wait 5 minutes...
    ↓
Attempt 2: After 5 minutes          ← Automatic
    ↓
  FAILED
    ↓
    Wait 15 minutes...
    ↓
Attempt 3: After 15 more minutes    ← Automatic (20 min total)
    ↓
  FAILED
    ↓
    Wait 45 minutes...
    ↓
Attempt 4: After 45 more minutes    ← Automatic (1hr 5min total)
    ↓
  FAILED
    ↓
    Wait 2.25 hours...
    ↓
Attempt 5: After 2.25 more hours    ← Automatic (3hr 20min total)
    ↓
  FAILED
    ↓
🔴 STOP - Flag as "Failed (max attempts)"
    Manual intervention required
```

**Why this approach?**
- Prevents API rate limiting
- Allows time for manual fixes
- Doesn't overwhelm logs
- Respects Meta's API guidelines

## 📚 Full Documentation

For detailed information:
- **Complete Guide**: `whatsappcrm_backend/products_and_services/META_CATALOG_SYNC_README.md`
- **Technical Summary**: `PRODUCT_SYNC_FIX_SUMMARY.md`

## 💡 Pro Tips

1. **Before creating many products**: Ensure Meta config is correct and test with one product first

2. **Image URLs must be public**: Meta's servers need to fetch the image without authentication

3. **Monitor sync status regularly**: Check the admin list view for any 🔴 or 🟠 indicators

4. **Use the reset action liberally**: It's safe to reset and retry after fixing issues

5. **Check logs for patterns**: If all products fail with the same error, it's a config issue

6. **SKU is mandatory**: Always set SKU before saving products

7. **Sync is automatic**: No need to manually trigger - just save the product

## ❓ FAQ

**Q: Does this fix the price format issue?**
A: That was fixed in a previous PR. This PR adds retry logic and admin visibility.

**Q: Will existing failed products automatically retry?**
A: No. Use the "Reset Meta sync attempts" action to retry them.

**Q: Can I disable auto-sync?**
A: Currently no. Set `is_active=False` to prevent sync for specific products.

**Q: What about the infinite loop?**
A: No loop exists. The logs you saw were normal WhatsApp message traffic.

**Q: How do I test if sync is working?**
A: Create a product with valid SKU, image, and price. Check admin status and logs.

**Q: Can I manually trigger sync?**
A: Just save the product. If it failed before, reset attempts first.

## 🆘 Need Help?

1. Check error message in admin (most common issues explained there)
2. Read `META_CATALOG_SYNC_README.md` for detailed troubleshooting
3. Test image URLs with curl
4. Verify Meta App Config settings
5. Check Meta API status at https://developers.facebook.com/status/

## ✅ Success Checklist

After deployment, verify:
- [ ] Migration ran successfully
- [ ] Backend restarted
- [ ] "Meta Sync Status" column visible in admin
- [ ] Can expand "Meta Catalog Sync Status" in product detail
- [ ] "Reset Meta sync attempts" action available
- [ ] Logs show bordered error format (if any errors)
- [ ] Existing failed products identified
- [ ] Root cause of failures understood
- [ ] Failed products reset and retried
- [ ] New products sync successfully

## 🎉 Done!

Your product sync is now production-ready with:
- ✅ Smart retry logic
- ✅ Error tracking
- ✅ Admin visibility
- ✅ Comprehensive logging
- ✅ Security validated

Enjoy seamless product syncing! 🚀
