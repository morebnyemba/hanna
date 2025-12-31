# Zoho Inventory Integration

This document describes the Zoho Inventory integration for syncing products and prices with the WhatsApp CRM backend.

## Overview

The Zoho Inventory integration allows you to:
- Sync products from Zoho Inventory to your WhatsApp CRM database
- Automatically update product prices, stock quantities, and descriptions
- Track synchronization status in the admin panel
- Trigger full or selective product syncs

## Architecture

The integration consists of several components:

### 1. Models (`integrations/models.py`)

**ZohoCredential** - Singleton model that stores Zoho API credentials:
- `client_id`: OAuth Client ID from Zoho
- `client_secret`: OAuth Client Secret
- `access_token`: Current OAuth access token
- `refresh_token`: Token for refreshing expired access tokens
- `expires_in`: Token expiration timestamp
- `scope`: OAuth permissions
- `organization_id`: Zoho organization/company ID
- `api_domain`: Zoho API endpoint (region-specific)

Key methods:
- `is_expired()`: Checks if the access token needs refreshing (with 5-minute buffer)
- `get_instance()`: Returns the singleton credential instance

### 2. OAuth Client (`integrations/utils.py`)

**ZohoClient** - Handles all Zoho API interactions:

Methods:
- `get_valid_token()`: Returns a valid access token, refreshing if needed
- `fetch_products(page, per_page)`: Fetches a single page of products from Zoho
- `fetch_all_products()`: Fetches all products, handling pagination automatically
- `_refresh_token()`: Refreshes the access token using the refresh token

### 3. Sync Logic (`products_and_services/services.py`)

**sync_zoho_products_to_db()** - Main synchronization function:
- Fetches all products from Zoho Inventory
- Maps Zoho fields to local Product model fields
- Uses `update_or_create` based on `zoho_item_id` for idempotent syncs
- Handles errors gracefully, continuing with remaining products
- Returns detailed statistics

Field mapping:
- `item_id` → `zoho_item_id`
- `name` → `name`
- `sku` → `sku`
- `description` → `description`
- `rate` → `price`
- `stock_on_hand` → `stock_quantity`
- `status` ('active') → `is_active`

### 4. Celery Task (`products_and_services/tasks.py`)

**task_sync_zoho_products** - Async task wrapper:
- Prevents UI freezing during large syncs
- Configured with 3 retries and 60-second delay
- Logs all operations for debugging

### 5. Admin Interface

**ZohoCredential Admin**:
- Single instance configuration (singleton pattern)
- Token status indicator (Valid/Expired/No Token)
- Secure display of credentials (truncated)
- Cannot be deleted (singleton protection)

**Product Admin Actions**:
- `sync_selected_items`: Placeholder for selective sync (requires API enhancement)

**Top Menu Button**:
- "Sync Zoho" button in Jazzmin admin top menu
- Triggers full product sync via Celery task
- Shows task ID for tracking

## Setup Instructions

### 1. Configure Zoho OAuth Application

1. Go to [Zoho API Console](https://api-console.zoho.com/)
2. Create a new "Server-based Application"
3. Note down your Client ID and Client Secret
4. Set up OAuth redirect URI (not needed for refresh token flow)

### 2. Generate Initial Tokens

You need to manually generate initial OAuth tokens using Zoho's OAuth flow:

```bash
# 1. Get authorization code (replace with your client ID and redirect URI)
https://accounts.zoho.com/oauth/v2/auth?scope=ZohoInventory.items.READ&client_id=YOUR_CLIENT_ID&response_type=code&access_type=offline&redirect_uri=YOUR_REDIRECT_URI

# 2. Exchange code for tokens
curl -X POST https://accounts.zoho.com/oauth/v2/token \
  -d "code=YOUR_AUTH_CODE" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=YOUR_REDIRECT_URI" \
  -d "grant_type=authorization_code"
```

This will return:
```json
{
  "access_token": "1000.xxx",
  "refresh_token": "1000.yyy",
  "expires_in": 3600,
  "token_type": "Bearer"
}
```

### 3. Configure in Django Admin

1. Navigate to Admin → Integrations → Zoho Credentials
2. Click "Add Zoho Credential" (only appears if none exists)
3. Fill in the form:
   - **Client ID**: Your Zoho OAuth Client ID
   - **Client Secret**: Your Zoho OAuth Client Secret
   - **Access Token**: The access_token from step 2
   - **Refresh Token**: The refresh_token from step 2
   - **Scope**: `ZohoInventory.items.READ` (default)
   - **Organization ID**: Your Zoho organization ID
   - **API Domain**: `https://inventory.zoho.com` (or `.eu`, `.in` based on region)
   - **Expires In**: Set to ~1 hour from now (will auto-refresh)
4. Save

### 4. Add zoho_item_id Field to Products

Run migrations to add the new field:

```bash
cd whatsappcrm_backend
python manage.py migrate integrations
python manage.py migrate products_and_services
```

### 5. Test the Integration

#### Option A: Using Admin UI
1. Go to Admin panel
2. Click "Sync Zoho" button in the top menu
3. Check messages for task ID
4. Monitor logs: `tail -f logs/django.log`

#### Option B: Using Django Shell
```python
from integrations.utils import ZohoClient
from products_and_services.services import sync_zoho_products_to_db

# Test API connection
client = ZohoClient()
result = client.fetch_products(page=1, per_page=10)
print(f"Fetched {len(result['items'])} items")

# Run sync
stats = sync_zoho_products_to_db()
print(f"Created: {stats['created']}, Updated: {stats['updated']}, Failed: {stats['failed']}")
```

#### Option C: Using Celery Task
```python
from products_and_services.tasks import task_sync_zoho_products

# Trigger async task
task = task_sync_zoho_products.delay()
print(f"Task ID: {task.id}")

# Check task status later
from celery.result import AsyncResult
result = AsyncResult(task.id)
print(f"Status: {result.status}")
if result.ready():
    print(f"Result: {result.result}")
```

## Usage

### Full Sync

**Via Admin UI:**
1. Click "Sync Zoho" in top menu
2. Wait for confirmation message with task ID
3. Check Products list to see synced items

**Via Management Command:**
```bash
python manage.py shell
>>> from products_and_services.tasks import task_sync_zoho_products
>>> task_sync_zoho_products.delay()
```

### Monitoring Sync Status

Check Product admin fields:
- **Zoho Item ID**: Populated after sync
- **Updated At**: Shows last sync time
- **Stock Quantity**: Updated from Zoho
- **Price**: Updated from Zoho

### Error Handling

The sync function handles errors gracefully:
- Individual product failures don't stop the entire sync
- Errors are logged with product details
- Statistics include failed count and error messages
- Check Django logs for detailed error information

### Troubleshooting

**Token Expired Error:**
- The system auto-refreshes tokens
- If refresh fails, re-generate tokens manually (see Setup step 2)
- Check that refresh_token is valid and not expired

**No Items Synced:**
- Verify organization_id is correct
- Check API domain matches your Zoho region
- Ensure Zoho account has items in Inventory
- Review Zoho API permissions/scope

**Duplicate SKU Errors:**
- Products use `zoho_item_id` as primary identifier
- SKU duplicates are allowed (set to None if empty)
- Manual products without zoho_item_id won't conflict

**Import Failures:**
- Check that `integrations` app is in INSTALLED_APPS
- Verify migrations are applied
- Ensure Celery is running for async tasks

## API Reference

### ZohoClient Methods

```python
client = ZohoClient()

# Fetch single page
result = client.fetch_products(page=1, per_page=200)
# Returns: {'items': [...], 'page_context': {...}}

# Fetch all products (paginated)
all_items = client.fetch_all_products()
# Returns: List[Dict] - all items from all pages

# Get valid token (auto-refreshes if needed)
token = client.get_valid_token()
# Returns: str - valid access token
```

### Sync Function

```python
from products_and_services.services import sync_zoho_products_to_db

stats = sync_zoho_products_to_db()
# Returns:
# {
#     'total': 150,        # Total items from Zoho
#     'created': 100,      # New products created
#     'updated': 50,       # Existing products updated
#     'failed': 0,         # Failed products
#     'errors': []         # List of error messages
# }
```

### Celery Task

```python
from products_and_services.tasks import task_sync_zoho_products

# Async execution
task = task_sync_zoho_products.delay()
print(task.id)  # Task ID for tracking

# Synchronous execution (for testing)
result = task_sync_zoho_products()
```

## Data Flow

```
Zoho Inventory API
        ↓
   ZohoClient
   (fetch_all_products)
        ↓
sync_zoho_products_to_db
   (maps fields)
        ↓
Product.objects.update_or_create
   (by zoho_item_id)
        ↓
   Local Database
```

## Security Considerations

1. **Credentials Storage**: Store client_secret securely (consider encryption at rest)
2. **Access Tokens**: Tokens are stored in database but have short expiration
3. **API Permissions**: Use minimal required scope (`ZohoInventory.items.READ`)
4. **Admin Access**: Only staff users can trigger syncs
5. **Token Refresh**: Automatic refresh prevents token expiration

## Performance

- **Batch Size**: Fetches 200 items per API call (Zoho max)
- **Pagination**: Automatic handling of multiple pages
- **Database Operations**: Uses `update_or_create` for efficiency
- **Async Execution**: Celery prevents blocking during large syncs
- **Error Recovery**: Individual failures don't block entire sync

## Future Enhancements

1. **Selective Sync**: Sync specific products by Zoho ID
2. **Bi-directional Sync**: Push local changes back to Zoho
3. **Scheduled Sync**: Periodic background sync via Celery Beat
4. **Webhook Integration**: Real-time updates from Zoho
5. **Product Categories**: Map Zoho categories to local categories
6. **Product Images**: Sync product images from Zoho
7. **Multi-currency**: Handle different currencies properly
8. **Inventory Tracking**: Real-time stock updates

## Support

For issues or questions:
1. Check Django logs: `logs/django.log`
2. Review Celery logs: `logs/celery.log`
3. Enable debug mode: Set `DEBUG=True` in `.env`
4. Test API connection in Django shell
5. Verify Zoho credentials in admin panel

## Dependencies

- `requests`: For API calls
- `celery`: For async task execution
- `django`: Core framework
- `djangorestframework`: For API serialization

All dependencies are listed in `requirements.txt`.
