# SSR Automation Implementation - Deployment Guide

## Overview
This implementation adds automatic SSR (Installation System Record) creation when solar packages are purchased. It includes compatibility validation, automatic warranty creation, customer portal access, and notifications.

## Files Modified

### Core Implementation
- `products_and_services/models.py` - Added `CompatibilityRule` model
- `products_and_services/admin.py` - Added admin interface for compatibility rules
- `products_and_services/services.py` - Added `CompatibilityValidationService` and `SolarOrderAutomationService`
- `products_and_services/signals.py` - Added `auto_create_ssr_for_solar_orders` signal handler
- `products_and_services/views.py` - Added `CompatibilityViewSet` API endpoints
- `products_and_services/urls.py` - Registered compatibility endpoints
- `products_and_services/serializers.py` - Added compatibility serializers

### Tests
- `products_and_services/test_ssr_automation.py` - Comprehensive test suite with 14 test cases

## Database Migrations

### Creating Migrations
Run the following command to create the migration for the new CompatibilityRule model:

```bash
# Using Docker
docker-compose exec backend python manage.py makemigrations products_and_services

# Or locally with virtual environment
cd whatsappcrm_backend
python manage.py makemigrations products_and_services
```

This will create a migration file like `0001_add_compatibility_rule_model.py` in `products_and_services/migrations/`.

### Applying Migrations
Apply the migrations to update the database schema:

```bash
# Using Docker
docker-compose exec backend python manage.py migrate

# Or locally
cd whatsappcrm_backend
python manage.py migrate
```

## Running Tests

### Run All SSR Automation Tests
```bash
# Using Docker
docker-compose exec backend python manage.py test products_and_services.test_ssr_automation

# Or locally
cd whatsappcrm_backend
python manage.py test products_and_services.test_ssr_automation
```

### Run Specific Test Classes
```bash
# Test compatibility rules
docker-compose exec backend python manage.py test products_and_services.test_ssr_automation.CompatibilityRuleModelTest

# Test compatibility validation service
docker-compose exec backend python manage.py test products_and_services.test_ssr_automation.CompatibilityValidationServiceTest

# Test SSR automation service
docker-compose exec backend python manage.py test products_and_services.test_ssr_automation.SSRAutomationServiceTest

# Test signal handler
docker-compose exec backend python manage.py test products_and_services.test_ssr_automation.SSRSignalHandlerTest
```

### Run All Products Tests
```bash
docker-compose exec backend python manage.py test products_and_services
```

## Configuration

### Environment Variables
No new environment variables are required. The system uses existing email and notification configurations.

### Email Configuration
Ensure the following are configured in `.env.prod`:
- `DEFAULT_FROM_EMAIL` - Email address for order confirmations
- `EMAIL_HOST` - SMTP host
- `EMAIL_PORT` - SMTP port
- `EMAIL_HOST_USER` - SMTP username
- `EMAIL_HOST_PASSWORD` - SMTP password

## Features

### 1. Compatibility Validation

#### API Endpoints

**Check Product Compatibility**
```bash
POST /crm-api/products/compatibility/check-products/
Content-Type: application/json

{
  "product_a_id": 1,
  "product_b_id": 2
}

Response:
{
  "product_a": {"id": 1, "name": "5kW Inverter", "sku": "INV-5KW"},
  "product_b": {"id": 2, "name": "5kWh Battery", "sku": "BAT-5KWH"},
  "compatible": true,
  "reason": "Compatible: These products work well together",
  "has_rule": true,
  "warning": false
}
```

**Validate Solar Package**
```bash
POST /crm-api/products/compatibility/validate-package/
Content-Type: application/json

{
  "package_id": 1
}

Response:
{
  "package": {"id": 1, "name": "5kW Complete System", "system_size": "5.00"},
  "compatibility": {
    "valid": true,
    "errors": [],
    "warnings": [],
    "compatibility_checks": [...]
  },
  "system_size": {"valid": true, "warnings": []},
  "overall_valid": true
}
```

### 2. Automatic SSR Creation

The system automatically creates an SSR when:
1. An order contains solar package products
2. Order stage is `CLOSED_WON`
3. Payment status is `PAID`

**What Gets Created:**
- InstallationSystemRecord (SSR)
- InstallationRequest (if not exists)
- Warranty records for each serialized item
- Customer portal User account
- Email confirmation to customer
- Notification to admin/branch staff

**Idempotency:**
- Multiple saves of the same order won't create duplicate SSRs
- Existing SSRs are detected and reused

### 3. Admin Interface

#### Managing Compatibility Rules
1. Log in to Django admin
2. Navigate to "Products and Services" → "Compatibility Rules"
3. Click "Add Compatibility Rule"
4. Fill in:
   - Name: Descriptive name (e.g., "5kW Inverter compatible with 5kWh Battery")
   - Product A: First product
   - Product B: Second product
   - Rule Type: COMPATIBLE, INCOMPATIBLE, or REQUIRES
   - Description: Explanation of the rule
   - Is Active: Check to enable the rule
5. Save

#### Example Rules
```
Name: "5kW Inverter compatible with 5kWh Battery"
Product A: 5kW Solar Inverter
Product B: 5kWh Lithium Battery
Rule Type: COMPATIBLE
Description: These products are designed to work together

---

Name: "5kW Inverter incompatible with 1kWh Battery"
Product A: 5kW Solar Inverter
Product B: 1kWh Battery
Rule Type: INCOMPATIBLE
Description: Battery capacity too small for this inverter
```

## Testing the Implementation

### Manual Testing Steps

1. **Create Test Data**
   ```bash
   docker-compose exec backend python manage.py shell
   ```
   
   ```python
   from products_and_services.models import Product, SolarPackage, SolarPackageProduct, CompatibilityRule
   from customer_data.models import Order, OrderItem, CustomerProfile
   from conversations.models import Contact
   from decimal import Decimal
   
   # Create products
   inverter = Product.objects.create(
       name='5kW Inverter Test',
       sku='TEST-INV-5KW',
       product_type='hardware',
       price=Decimal('1500.00'),
       is_active=True
   )
   
   battery = Product.objects.create(
       name='5kWh Battery Test',
       sku='TEST-BAT-5KWH',
       product_type='hardware',
       price=Decimal('2500.00'),
       is_active=True
   )
   
   # Create compatibility rule
   rule = CompatibilityRule.objects.create(
       name='Test Compatibility',
       product_a=inverter,
       product_b=battery,
       rule_type='compatible',
       is_active=True
   )
   
   # Create solar package
   package = SolarPackage.objects.create(
       name='Test 5kW System',
       system_size=Decimal('5.0'),
       price=Decimal('8000.00'),
       is_active=True
   )
   
   SolarPackageProduct.objects.create(
       solar_package=package,
       product=inverter,
       quantity=1
   )
   
   SolarPackageProduct.objects.create(
       solar_package=package,
       product=battery,
       quantity=2
   )
   ```

2. **Create Test Order**
   ```python
   # Create customer
   contact = Contact.objects.create(whatsapp_id='+263771234567')
   customer = CustomerProfile.objects.create(
       contact=contact,
       first_name='Test',
       last_name='Customer',
       email='test@example.com',
       address_line_1='123 Test St',
       city='Test City',
       country='Test Country'
   )
   
   # Create order
   order = Order.objects.create(
       customer=customer,
       stage='closed_won',
       payment_status='paid',
       amount=Decimal('8000.00'),
       order_number='TEST-ORDER-001'
   )
   
   # Add order items
   OrderItem.objects.create(
       order=order,
       product=inverter,
       quantity=1,
       unit_price=inverter.price,
       total_amount=inverter.price
   )
   
   OrderItem.objects.create(
       order=order,
       product=battery,
       quantity=2,
       unit_price=battery.price,
       total_amount=battery.price * 2
   )
   
   # Trigger SSR creation
   order.save()
   ```

3. **Verify SSR Creation**
   ```python
   from installation_systems.models import InstallationSystemRecord
   
   # Check if SSR was created
   ssr = InstallationSystemRecord.objects.filter(order=order).first()
   print(f"SSR Created: {ssr}")
   print(f"SSR ID: {ssr.short_id if ssr else 'None'}")
   print(f"Installation Request: {ssr.installation_request if ssr else 'None'}")
   print(f"Warranties: {ssr.warranties.count() if ssr else 0}")
   ```

4. **Test API Endpoints**
   ```bash
   # Check product compatibility
   curl -X POST http://localhost:8000/crm-api/products/compatibility/check-products/ \
     -H "Content-Type: application/json" \
     -d '{"product_a_id": 1, "product_b_id": 2}'
   
   # Validate package
   curl -X POST http://localhost:8000/crm-api/products/compatibility/validate-package/ \
     -H "Content-Type: application/json" \
     -d '{"package_id": 1}'
   ```

## Monitoring and Logging

### Check Logs
```bash
# View backend logs
docker-compose logs -f backend

# View logs for SSR creation
docker-compose logs backend | grep "SSR"
docker-compose logs backend | grep "auto-created"
```

### Log Messages
The system logs the following events:
- SSR creation: `"Successfully auto-created SSR {ssr_id} for order {order_id}"`
- Duplicate prevention: `"Duplicate SSR creation attempted for order {order_id}"`
- Validation failures: `"Compatibility validation failed for order {order_id}"`
- Portal access granted: `"Granted portal access to customer {customer_id}"`
- Email sent: `"Sent order confirmation email for order {order_id}"`
- Notifications created: `"Created notification for admin {username}"`

## Troubleshooting

### SSR Not Created
1. Check order status: Must be `CLOSED_WON` with `PAID` payment status
2. Check if order contains solar products
3. Check logs for errors
4. Verify compatibility validation passed

### Duplicate SSRs
- The system prevents duplicates automatically
- If duplicates exist, check database for SSRs with same order_id
- Clean up duplicates manually if needed

### Compatibility Validation Failing
1. Check compatibility rules in admin
2. Verify rules are active
3. Check product pairs in the package
4. Review validation errors in order notes

### Email Not Sending
1. Verify email configuration in `.env.prod`
2. Check customer has valid email address
3. Review email logs
4. Test SMTP connection

## Rollback Plan

If issues occur after deployment:

1. **Disable Signal Handler**
   ```python
   # In signals.py, comment out the signal handler
   # @receiver(post_save, sender=Order)
   # def auto_create_ssr_for_solar_orders(sender, instance, created, **kwargs):
   #     ...
   ```

2. **Revert Migrations**
   ```bash
   docker-compose exec backend python manage.py migrate products_and_services <previous_migration>
   ```

3. **Manual SSR Creation**
   If automatic creation is disabled, SSRs can be created manually via Django admin or API.

## Performance Considerations

- Signal handler runs on every Order save - optimized with early returns
- Compatibility validation only runs for solar packages
- Database queries are optimized with select_related() and prefetch_related()
- No external API calls during SSR creation (async email/notifications)

## Security Considerations

- Customer portal passwords are randomly generated and must be reset
- Email confirmations include SSR ID but no sensitive data
- Admin notifications only go to staff/superusers
- Compatibility validation prevents unsafe system configurations

## Support

For issues or questions:
1. Check logs first
2. Review test suite for expected behavior
3. Verify configuration settings
4. Contact development team if issues persist
