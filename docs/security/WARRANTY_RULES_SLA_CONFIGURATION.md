# Warranty Rules & SLA Configuration

## Overview

This implementation adds comprehensive warranty rules and Service Level Agreement (SLA) configuration and tracking to the HANNA CRM system. It enables:

- **Automated Warranty Duration Assignment**: Configure warranty durations by product or category, automatically applied when warranties are created
- **SLA Threshold Management**: Define response and resolution time expectations for different request types
- **Automatic SLA Tracking**: Real-time monitoring of SLA compliance with breach detection
- **Escalation & Alerts**: Configurable notifications when approaching or breaching SLA deadlines
- **Dashboard Metrics**: Compliance reporting for management visibility

## Features Implemented

### 1. Warranty Rules

#### Model: `WarrantyRule`
Configurable rules that automatically assign warranty durations to products.

**Fields:**
- `name`: Descriptive name for the rule
- `product`: Specific product (optional - use product OR category)
- `product_category`: Product category (optional - use product OR category)
- `warranty_duration_days`: Number of days warranty is valid
- `terms_and_conditions`: Specific terms for this warranty
- `is_active`: Whether the rule is currently active
- `priority`: Higher priority rules take precedence (0 is lowest)

**Rule Selection Logic:**
1. Product-specific rules take precedence over category rules
2. Among multiple rules of the same type, higher priority wins
3. Inactive rules are never applied

**Example Usage:**
```python
# Create a warranty rule for all solar panels
WarrantyRule.objects.create(
    name='Solar Panel Standard Warranty',
    product_category=solar_category,
    warranty_duration_days=730,  # 2 years
    is_active=True,
    priority=1
)

# Override for a specific high-end product
WarrantyRule.objects.create(
    name='Premium Solar Panel Extended Warranty',
    product=premium_solar_panel,
    warranty_duration_days=1825,  # 5 years
    is_active=True,
    priority=10  # Higher priority
)
```

### 2. SLA Thresholds

#### Model: `SLAThreshold`
Defines service level expectations for different types of requests.

**Fields:**
- `name`: Descriptive name for the SLA
- `request_type`: Type of request (installation, service, warranty_claim, site_assessment)
- `response_time_hours`: Max hours for initial response
- `resolution_time_hours`: Max hours for complete resolution
- `escalation_rules`: JSON or text describing escalation procedures
- `notification_threshold_percent`: Send alerts at this % of time elapsed (e.g., 80)
- `is_active`: Whether this SLA is currently active

**Request Types:**
- `installation` - Installation requests
- `service` - Service requests
- `warranty_claim` - Warranty claims
- `site_assessment` - Site assessment requests

**Example Usage:**
```python
# Create SLA for installation requests
SLAThreshold.objects.create(
    name='Standard Installation SLA',
    request_type='installation',
    response_time_hours=24,  # Respond within 24 hours
    resolution_time_hours=72,  # Complete within 3 days
    notification_threshold_percent=80,  # Alert at 80% elapsed
    is_active=True
)

# Create SLA for urgent warranty claims
SLAThreshold.objects.create(
    name='Warranty Claim SLA',
    request_type='warranty_claim',
    response_time_hours=48,
    resolution_time_hours=120,
    escalation_rules='Escalate to manager after 96 hours',
    notification_threshold_percent=75,
    is_active=True
)
```

### 3. SLA Status Tracking

#### Model: `SLAStatus`
Automatically tracks SLA compliance for individual requests.

**Fields:**
- `sla_threshold`: The SLA threshold being tracked
- `content_type` / `object_id`: Generic relation to tracked request
- `request_created_at`: When the request was created
- `response_time_deadline`: Calculated response deadline
- `resolution_time_deadline`: Calculated resolution deadline
- `response_completed_at`: When response was completed (nullable)
- `resolution_completed_at`: When resolution was completed (nullable)
- `response_status`: Current response status (compliant, warning, breached)
- `resolution_status`: Current resolution status (compliant, warning, breached)
- `last_notification_sent`: Last time a notification was sent

**Status Types:**
- `compliant`: Within SLA deadlines
- `warning`: Approaching deadline (based on notification_threshold_percent)
- `breached`: Past deadline

**Automatic Status Updates:**
The `update_status()` method automatically calculates current status based on:
- Current time vs. deadlines
- Whether response/resolution is completed
- Configured notification thresholds

## Business Logic Services

### WarrantyRuleService

Located in `warranty/services.py`, provides business logic for warranty rule application.

**Key Methods:**

```python
# Find the most applicable warranty rule for a product
rule = WarrantyRuleService.find_applicable_rule(product)

# Apply rule to an existing warranty
applied_rule, was_applied = WarrantyRuleService.apply_rule_to_warranty(warranty)

# Calculate warranty end date without creating a warranty
end_date = WarrantyRuleService.calculate_warranty_end_date(product, start_date)
```

### SLAService

Located in `warranty/services.py`, provides business logic for SLA tracking.

**Key Methods:**

```python
# Get active SLA threshold for a request type
threshold = SLAService.get_sla_threshold_for_request('installation')

# Create SLA status for a new request
sla_status = SLAService.create_sla_status(
    request_object=installation_request,
    request_type='installation',
    created_at=installation_request.created_at
)

# Mark response completed
SLAService.mark_response_completed(installation_request)

# Mark resolution completed
SLAService.mark_resolution_completed(installation_request)

# Get current SLA status
sla_status = SLAService.get_sla_status(installation_request)

# Get overall compliance metrics
metrics = SLAService.get_sla_compliance_metrics()
# Returns: {
#     'total_requests': 100,
#     'response_compliant': 85,
#     'response_warning': 10,
#     'response_breached': 5,
#     'resolution_compliant': 80,
#     'resolution_warning': 15,
#     'resolution_breached': 5,
#     'overall_compliance_rate': 80.00
# }
```

## Automatic Warranty Rule Application

Warranty rules are automatically applied when warranties are created via Django signals.

**Signal:** `warranty/signals.py`

```python
@receiver(post_save, sender=Warranty)
def apply_warranty_rule(sender, instance, created, **kwargs):
    """
    Automatically apply warranty rule when a warranty is created.
    Only applies if end_date equals start_date.
    """
```

**How it works:**
1. When a warranty is created with `end_date == start_date`
2. System finds the most applicable warranty rule
3. Calculates `end_date = start_date + rule.warranty_duration_days`
4. Saves the warranty with the calculated end date
5. Logs the applied rule for audit trail

**Override Capability:**
To override automatic rule application, simply set a specific `end_date` different from `start_date` when creating the warranty.

## SLA Monitoring Task

**Background Task:** `warranty/tasks.py` - `monitor_sla_compliance`

Runs every hour via Celery Beat to:
1. Get all active SLA statuses (not yet resolved)
2. Update status for each (check if breached, warning, etc.)
3. Send notifications if needed based on:
   - Status is WARNING or BREACHED
   - Not sent recently (1 hour for warnings, 4 hours for breaches)
4. Log notification activity

**Celery Beat Configuration:**
```python
# In settings.py
CELERY_BEAT_SCHEDULE = {
    'monitor-sla-compliance': {
        'task': 'warranty.tasks.monitor_sla_compliance',
        'schedule': crontab(minute=0, hour='*'),  # Every hour
    },
}
```

## API Endpoints

All endpoints are under `/api/admin/` and require admin authentication.

### Warranty Rules

**List warranty rules:**
```
GET /api/admin/warranty-rules/
```
Query parameters:
- `is_active=true/false` - Filter by active status
- `product=<id>` - Filter by product
- `product_category=<id>` - Filter by category
- `search=<term>` - Search in name, product name, category name
- `ordering=-priority` - Order results

**Create warranty rule:**
```
POST /api/admin/warranty-rules/
Content-Type: application/json

{
    "name": "Solar Panel Standard Warranty",
    "product_category": 5,
    "warranty_duration_days": 730,
    "terms_and_conditions": "Standard terms apply",
    "is_active": true,
    "priority": 1
}
```

**Update warranty rule:**
```
PUT /api/admin/warranty-rules/<id>/
Content-Type: application/json

{
    "name": "Updated Warranty Rule",
    "warranty_duration_days": 1095,
    ...
}
```

**Delete warranty rule:**
```
DELETE /api/admin/warranty-rules/<id>/
```

### SLA Thresholds

**List SLA thresholds:**
```
GET /api/admin/sla-thresholds/
```
Query parameters:
- `is_active=true/false`
- `request_type=installation/service/warranty_claim/site_assessment`
- `search=<term>`

**Create SLA threshold:**
```
POST /api/admin/sla-thresholds/
Content-Type: application/json

{
    "name": "Installation SLA",
    "request_type": "installation",
    "response_time_hours": 24,
    "resolution_time_hours": 72,
    "notification_threshold_percent": 80,
    "is_active": true
}
```

**Update SLA threshold:**
```
PUT /api/admin/sla-thresholds/<id>/
PATCH /api/admin/sla-thresholds/<id>/
```

**Delete SLA threshold:**
```
DELETE /api/admin/sla-thresholds/<id>/
```

### SLA Status

**List SLA statuses:**
```
GET /api/admin/sla-statuses/
```
Query parameters:
- `response_status=compliant/warning/breached`
- `resolution_status=compliant/warning/breached`
- `sla_threshold__request_type=<type>`

**Get compliance metrics (Dashboard Widget):**
```
GET /api/admin/sla-statuses/compliance_metrics/

Response:
{
    "total_requests": 100,
    "response_compliant": 85,
    "response_warning": 10,
    "response_breached": 5,
    "resolution_compliant": 80,
    "resolution_warning": 15,
    "resolution_breached": 5,
    "overall_compliance_rate": 80.00
}
```

## Django Admin Interface

All models are registered in Django admin with proper configurations:

### WarrantyRule Admin
- List view shows: name, product, category, duration, active status, priority
- Filters: active status, category
- Search: name, product name, category name
- Organized fieldsets for easy data entry
- Validation prevents both product and category being set

### SLAThreshold Admin
- List view shows: name, request type, response/resolution times, threshold %
- Filters: active status, request type
- Search: name
- Organized fieldsets with helpful descriptions

### SLAStatus Admin (Read-Only)
- List view shows: threshold, request info, statuses, created date
- Filters: response status, resolution status, request type
- Cannot add or delete (automatically created/managed)
- Detailed fieldsets showing all tracking information

## Testing

Comprehensive test suite in `warranty/tests.py`:

**Test Coverage:**
- WarrantyRule model creation and validation
- WarrantyRule service methods (find, apply, calculate)
- SLAThreshold model creation and representation
- SLAService methods (create, mark completed, get status, metrics)
- SLAStatus status updates and breach detection
- API endpoints for all CRUD operations
- Compliance metrics endpoint

**Running Tests:**
```bash
cd whatsappcrm_backend
python manage.py test warranty
```

**Test Results:**
- 12 core tests passing (models, services, API endpoints)
- Additional tests require Redis/Celery infrastructure (expected in production)

## Usage Examples

### Example 1: Set up warranty rules for products

```python
# Create category rule for all solar panels
solar_category = ProductCategory.objects.get(name='Solar Panels')
WarrantyRule.objects.create(
    name='Solar Panel Standard Warranty',
    product_category=solar_category,
    warranty_duration_days=730,  # 2 years
    is_active=True,
    priority=1
)

# Create specific rule for premium product
premium_panel = Product.objects.get(sku='SP-PREMIUM-500W')
WarrantyRule.objects.create(
    name='Premium Panel Extended Warranty',
    product=premium_panel,
    warranty_duration_days=1825,  # 5 years
    is_active=True,
    priority=10
)

# Create warranty - rule applied automatically
serialized_item = SerializedItem.objects.get(serial_number='SN123456')
warranty = Warranty.objects.create(
    serialized_item=serialized_item,
    customer=customer,
    start_date=date.today(),
    end_date=date.today()  # Same as start - triggers auto-application
)
# warranty.end_date will be automatically set based on the rule
```

### Example 2: Configure SLA tracking for installations

```python
# Create SLA threshold
SLAThreshold.objects.create(
    name='Standard Installation SLA',
    request_type='installation',
    response_time_hours=24,
    resolution_time_hours=72,
    notification_threshold_percent=80,
    is_active=True
)

# When installation request is created, manually create SLA tracking
installation = InstallationRequest.objects.create(
    customer=customer,
    status='pending',
    installation_type='solar'
)

# Create SLA status
from warranty.services import SLAService
sla_status = SLAService.create_sla_status(
    request_object=installation,
    request_type='installation'
)

# Later, mark milestones
SLAService.mark_response_completed(installation)
# ... work happens ...
SLAService.mark_resolution_completed(installation)
```

### Example 3: Check SLA compliance from dashboard

```python
from warranty.services import SLAService

# Get overall metrics
metrics = SLAService.get_sla_compliance_metrics()
print(f"Overall compliance rate: {metrics['overall_compliance_rate']}%")
print(f"Breached requests: {metrics['resolution_breached']}")

# Get SLA status for specific request
sla_status = SLAService.get_sla_status(installation_request)
if sla_status:
    print(f"Response status: {sla_status.response_status}")
    print(f"Resolution status: {sla_status.resolution_status}")
    if sla_status.response_status == 'breached':
        print("⚠️ Response SLA breached!")
```

## Database Migrations

```bash
cd whatsappcrm_backend
python manage.py makemigrations warranty
python manage.py migrate
```

This creates:
- `WarrantyRule` table with indexes on active status and priority
- `SLAThreshold` table with unique constraint on (request_type, name)
- `SLAStatus` table with indexes on statuses and content_type/object_id

## Security Considerations

1. **Admin-only access**: All warranty rule and SLA configuration endpoints require admin authentication
2. **Read-only SLA status**: SLA statuses cannot be manually created or deleted through admin - only viewed
3. **Validation**: WarrantyRule model validates that either product OR category is set, not both
4. **Audit trail**: All models include created_at and updated_at timestamps

## Performance Considerations

1. **Efficient queries**: Use `select_related()` in viewsets to minimize database queries
2. **Indexed fields**: Database indexes on commonly filtered fields (status, request_type, etc.)
3. **Hourly monitoring**: SLA monitoring runs once per hour to balance responsiveness and system load
4. **Notification throttling**: Prevents spam by limiting notification frequency

## Future Enhancements

Potential improvements for future iterations:

1. **Custom escalation workflows**: Define multi-tier escalation based on breach severity
2. **SLA exemptions**: Allow marking specific requests as exempt from SLA tracking
3. **Historical reporting**: Track SLA compliance trends over time
4. **Business hours**: Calculate SLA deadlines based on business hours, not calendar days
5. **Multiple notification channels**: SMS, WhatsApp, email for SLA alerts
6. **Warranty terms templates**: Reusable templates for common warranty terms
7. **Auto-create SLA status**: Use signals to automatically create SLA status for new requests

## Troubleshooting

**Issue: Warranty rule not applying**
- Check that rule is active (`is_active=True`)
- Verify product or category matches
- Check priority if multiple rules exist
- Ensure `end_date == start_date` when creating warranty

**Issue: SLA notifications not sending**
- Verify Celery Beat is running
- Check Redis connection
- Review logs for `monitor_sla_compliance` task
- Ensure SMTP is configured for email notifications

**Issue: SLA status not updating**
- Call `sla_status.update_status()` manually
- Wait for hourly monitoring task to run
- Check that SLA threshold is active

## Support

For questions or issues:
1. Check this documentation
2. Review test cases in `warranty/tests.py`
3. Check logs for error messages
4. Contact the development team

## Related Documentation

- `WARRANTY_PDF_QUICKSTART.md` - Warranty certificate generation
- `ADMIN_API_ENDPOINTS.md` - Complete API reference
- `CELERY.md` - Celery configuration and tasks
- `README.md` - Main project documentation
