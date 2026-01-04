# Deployment Instructions for PR: Fix Zoho API Domain and Allow OrderItems Without Products

## Changes Summary
This PR fixes two issues:
1. **Zoho API Domain Error**: Updated to use the correct `zohoapis.com` domain
2. **OrderItems Without Products**: OrderItems can now be created even when products don't exist

## Pre-Deployment Steps

### 1. Review Documentation
- Read `ZOHO_API_DOMAIN_FIX.md` for detailed information about the changes
- Understand the impact on invoice and job card processing
- Review database migration requirements

### 2. Backup Database (CRITICAL)
```bash
# Create a backup of your database before deploying - MIGRATIONS REQUIRED
docker compose exec db pg_dump -U your_user your_database > backup_$(date +%Y%m%d_%H%M%S).sql
```

## Deployment Steps

### 1. Pull Latest Changes
```bash
git pull origin main
```

### 2. Run Database Migrations (REQUIRED)
```bash
# Generate and apply migrations for new OrderItem fields
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

### 3. Restart Backend Services
```bash
docker compose restart backend
docker compose restart celery
```

### 3. Update Zoho API Domain (CRITICAL)

You MUST update the API domain for existing installations:

**Via Django Admin:**
1. Go to Admin → Integrations → Zoho Credentials
2. Edit your existing credential
3. Update the **API Domain** field:
   - Old: `https://inventory.zoho.com`
   - New: `https://inventory.zohoapis.com`
   - (Use appropriate regional domain if not .com)
4. Save the changes

**Via Django Shell:**
```bash
docker compose exec backend python manage.py shell

from integrations.models import ZohoCredential
cred = ZohoCredential.get_instance()
cred.api_domain = 'https://inventory.zohoapis.com'
cred.save()
print(f"Updated to: {cred.api_domain}")
exit()
```

### 4. Sync Products from Zoho (Recommended)

After updating the API domain, sync your products:

1. Go to Django Admin
2. Click "Sync Zoho" button in the top menu
3. Wait for completion
4. Verify products were synced successfully

### 5. Link Existing OrderItems to Products (Optional)

If you have OrderItems created before syncing products:

```bash
docker compose exec backend python manage.py shell

from customer_data.models import OrderItem
from products_and_services.models import Product

# Find OrderItems without products
unlinked = OrderItem.objects.filter(product__isnull=True)
print(f"Found {unlinked.count()} unlinked OrderItems")

# Example: Link by SKU
for item in unlinked:
    if item.product_sku:
        product = Product.objects.filter(sku=item.product_sku).first()
        if product:
            item.product = product
            item.save()
            print(f"Linked OrderItem {item.id} to Product {product.name}")
```

## Post-Deployment Verification

### 1. Test Database Migrations
```bash
# Verify migrations applied successfully
docker compose exec backend python manage.py showmigrations customer_data
```

Expected output should show all migrations as [X] (applied).

### 2. Test Zoho Sync
```bash
# Check Celery logs for successful sync
docker compose logs celery --tail=100 | grep "Zoho"
```

Expected output:
- "Successfully fetched X items from Zoho Inventory"
- No 400 errors about API domain

### 3. Test Invoice Processing

**Important:** Invoices now create OrderItems WITHOUT automatically creating products.

Test flow:
1. Send a test invoice via email
2. Check that:
   - Order is created successfully
   - OrderItems are created for all line items
   - OrderItems with product=None have product_sku and product_description filled
   - No products are automatically created
3. Link products manually:
   - Sync products from Zoho
   - Use Django Admin to link OrderItems to products
   - Or use the shell script above


### 4. Monitor Logs

Watch for these log messages:
- "Created OrderItem without product for SKU 'XXX'" - indicates OrderItem created without product
- "Product not found..." - informational, products can be linked later

## Rollback Plan

If issues occur after deployment:

### Quick Rollback (Not Recommended - Migrations)
```bash
# Note: This won't undo database migrations automatically
git revert HEAD
docker compose exec backend python manage.py migrate customer_data <previous_migration>
docker compose restart backend
docker compose restart celery
```

### Restore API Domain
If you need to use the old API domain (not recommended):
```bash
docker compose exec backend python manage.py shell

from integrations.models import ZohoCredential
cred = ZohoCredential.get_instance()
cred.api_domain = 'https://inventory.zoho.com'  # Old domain
cred.save()
exit()
```

Note: The old domain may not work as Zoho has deprecated it.

## Known Issues & Solutions

### Issue: OrderItems without products
**Solution:** This is expected behavior. Link products by:
1. Syncing from Zoho
2. Manually creating products in Django Admin
3. Using the shell script to auto-link by SKU
4. Query: `OrderItem.objects.filter(product__isnull=True)` to find unlinked items

### Issue: Existing code expects product to always be set
**Solution:** 
1. Update code to check if `order_item.product is not None` before accessing
2. Use `order_item.product.name if order_item.product else order_item.product_description`
3. Review serializers and views that return OrderItems

### Issue: Zoho sync still returns 400 error
**Solution:** 
1. Verify API domain is updated correctly
2. Check that domain uses `zohoapis.com` not `zoho.com`
3. Verify OAuth tokens are still valid

## Support

If you encounter issues:
1. Check Django logs: `docker compose logs backend --tail=100`
2. Check Celery logs: `docker compose logs celery --tail=100`
3. Review `ZOHO_API_DOMAIN_FIX.md` for detailed troubleshooting
4. Contact the development team with log outputs

## Maintenance Notes

### Regular Tasks
1. **Product Sync**: Run "Sync Zoho" regularly to sync products and link OrderItems
2. **Link Unlinked OrderItems**: Periodically check and link OrderItems without products
3. **Monitor Unlinked Items**: Query `OrderItem.objects.filter(product__isnull=True).count()`
4. **Create Missing Products**: For custom/one-off items, create products manually

### SQL Queries for Monitoring
```sql
-- Find OrderItems without products
SELECT COUNT(*) FROM customer_data_orderitem WHERE product_id IS NULL;

-- Find OrderItems with SKU but no product
SELECT id, product_sku, product_description, unit_price 
FROM customer_data_orderitem 
WHERE product_id IS NULL AND product_sku IS NOT NULL;
```

### Future Considerations
- Set up automated Zoho sync (e.g., via Celery Beat) to ensure products exist before invoices arrive
- Create a background task to auto-link OrderItems after products are synced
- Add admin action to bulk-link OrderItems by SKU
- Consider adding validation warnings in admin for OrderItems without products
