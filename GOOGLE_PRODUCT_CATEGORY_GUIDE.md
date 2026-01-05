# Google Product Category for Meta Catalog

## Overview

This guide explains how to use the `google_product_category` field to categorize products when syncing to Meta (Facebook/WhatsApp) Catalog.

## What is Google Product Category?

The `google_product_category` field is a standardized taxonomy used by Meta to categorize products in their catalog. It helps:
- Improve product discoverability in WhatsApp and Facebook Shops
- Enable better ad targeting and campaign performance
- Ensure compliance with platform policies (especially for regulated categories like alcohol, apparel, etc.)
- Calculate correct taxes for transactions

## How to Set Product Category

### In Django Admin

1. Go to Django Admin → Products and Services → Products
2. Click on a product to edit it
3. Find the **Google Product Category** field in the main section
4. Enter either:
   - **Category Path**: e.g., `Apparel & Accessories > Clothing > Shirts & Tops`
   - **Category ID**: e.g., `212` (for Shirts & Tops)

### Field Format

The field accepts two formats:

1. **Text Path** (recommended for readability):
   ```
   Apparel & Accessories > Clothing > Shirts & Tops
   ```

2. **Numeric ID** (more compact):
   ```
   212
   ```

Both formats are valid and will be sent to Meta as-is.

## Best Practices

1. **Be Specific**: Use at least 2-3 levels deep in the category hierarchy
   - ✅ Good: `Electronics > Computers > Laptops`
   - ❌ Too broad: `Electronics`

2. **Match Your Product**: Choose the most specific category that describes your product
   - Solar panels → `Electronics > Renewable Energy > Solar Panels`
   - Accounting software → `Software > Business & Productivity > Accounting`

3. **Consistency**: Use the same category for similar products to improve analytics

4. **Compliance**: For regulated products (alcohol, tobacco, healthcare), accurate categorization is required

## Finding the Right Category

### Official Google Product Taxonomy

Download the official taxonomy from:
- **Text format**: https://www.google.com/basepages/producttype/taxonomy-with-ids.en-US.txt
- **Excel format**: Available in Google Merchant Center Help

### Common Categories for HANNA Products

Based on the business focus, here are some relevant categories:

#### Solar & Renewable Energy
- `Electronics > Renewable Energy > Solar Panels` (ID: 7380)
- `Electronics > Renewable Energy > Solar Inverters` (ID: 6910)
- `Electronics > Renewable Energy > Solar Batteries` (ID: 6911)

#### Software
- `Software > Business & Productivity > Accounting` (ID: 4196)
- `Software > Business & Productivity > CRM` (ID: 4197)
- `Software > Business & Productivity > ERP` (ID: 4198)

#### Hardware
- `Electronics > Computers > Laptops` (ID: 328)
- `Electronics > Computers > Desktops` (ID: 325)
- `Electronics > Networking > Routers` (ID: 279)

#### Services
- `Business & Industrial > Commercial Services > Consulting` (ID: 3250)
- `Business & Industrial > Commercial Services > Installation` (ID: 3251)

## Integration with Meta Catalog

When a product is synced to Meta Catalog (via the "Sync to Meta Catalog" admin action or automatic sync), the `google_product_category` is included in the API request if set.

### What Happens If Not Set?

- Meta will attempt to auto-categorize based on product name, description, and images
- Auto-categorization may not be as accurate as manual assignment
- Some features may not work optimally without proper categorization

### Syncing Products

1. **Automatic Sync**: When a product with images is saved, it's automatically synced to Meta
2. **Manual Sync**: Use the "Sync selected products to Meta Catalog" action in the product list
3. **Update Visibility**: After categorizing, you can use the visibility actions to publish/hide products

## Verification

To verify your products are properly categorized in Meta:

1. Log in to Meta Business Manager
2. Go to Commerce Manager → Catalog
3. View your products and check the category column
4. Filter by category to ensure proper grouping

## Migration Note

**For existing deployments:**

After pulling these changes, you'll need to:

1. Create and run migrations:
   ```bash
   cd whatsappcrm_backend
   python manage.py makemigrations products_and_services
   python manage.py migrate
   ```

2. (Optional) Update existing products with appropriate categories via Django Admin

3. Re-sync products to Meta to update their categories:
   ```
   Admin → Products → Select products → Actions → Sync selected products to Meta Catalog
   ```

## Troubleshooting

### Product Not Appearing in Meta Catalog

1. Check that `google_product_category` is set
2. Verify the category name/ID is valid (use the official taxonomy)
3. Check Meta Catalog sync logs in the admin for errors

### Invalid Category Error

- Ensure you're using the exact category path or ID from the official Google taxonomy
- Avoid typos in category names
- Use the numeric ID if the text format causes issues

## Support

For more information:
- Meta Product Catalog Docs: https://developers.facebook.com/docs/marketing-api/catalog
- Google Product Taxonomy: https://support.google.com/merchants/answer/6324436

## Example Usage

```python
# In Django shell or management command
from products_and_services.models import Product

# Update a product with category
product = Product.objects.get(sku='SOLAR-PANEL-100W')
product.google_product_category = 'Electronics > Renewable Energy > Solar Panels'
product.save()  # This will trigger sync to Meta if images are present

# Or use the category ID
product.google_product_category = '7380'
product.save()
```
