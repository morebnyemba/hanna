# Django ORM Relationship Paths Reference

This document provides a quick reference for correct Django ORM relationship paths in the HANNA WhatsApp CRM system.

## Product Model Relationships

### Path 1: Product → InstallationRequest
**Use Case**: Count installations related to a product through orders

**Relationship Chain**:
1. `Product` → `OrderItem` (via `order_items` related_name from `OrderItem.product` ForeignKey)
2. `OrderItem` → `Order` (via `order` field with `items` related_name)
3. `Order` → `InstallationRequest` (via `installation_requests` related_name from `InstallationRequest.associated_order` ForeignKey)

**Correct ORM Path**: `order_items__order__installation_requests`

**Example Usage**:
```python
from django.db.models import Count, Q
from products_and_services.models import Product

products = Product.objects.annotate(
    installations_count=Count(
        'order_items__order__installation_requests',
        filter=Q(order_items__order__installation_requests__status='completed'),
        distinct=True
    )
)
```

### Path 2: Product → WarrantyClaim
**Use Case**: Count warranty claims (faults) for a product

**Relationship Chain**:
1. `Product` → `SerializedItem` (via `serialized_items` related_name from `SerializedItem.product` ForeignKey)
2. `SerializedItem` → `Warranty` (via `warranty` OneToOne with `warranty` related_name)
3. `Warranty` → `WarrantyClaim` (via `claims` related_name from `WarrantyClaim.warranty` ForeignKey)

**Correct ORM Path**: `serialized_items__warranty__claims`

**Example Usage**:
```python
from django.db.models import Count
from products_and_services.models import Product

products = Product.objects.annotate(
    fault_count=Count(
        'serialized_items__warranty__claims',
        distinct=True
    )
)
```

### Path 3: WarrantyClaim → Product (Reverse)
**Use Case**: Filter warranty claims by product

**Relationship Chain (Reverse)**:
1. `WarrantyClaim` → `Warranty` (via `warranty` ForeignKey)
2. `Warranty` → `SerializedItem` (via `serialized_item` OneToOne field)
3. `SerializedItem` → `Product` (via `product` ForeignKey)

**Correct ORM Path**: `warranty__serialized_item__product`

**Example Usage**:
```python
from warranty.models import WarrantyClaim

# Get all warranty claims for a specific product
product_claims = WarrantyClaim.objects.filter(
    warranty__serialized_item__product=product
)

# Get common fault descriptions for a product
common_faults = WarrantyClaim.objects.filter(
    warranty__serialized_item__product=product
).values_list('description_of_fault', flat=True).distinct()[:3]
```

## Common Mistakes to Avoid

### ❌ Incorrect: Using model class name instead of related_name
```python
# WRONG - 'orderitem' is not the related_name
'orderitem__order__installation_requests'

# CORRECT - 'order_items' is the related_name defined in OrderItem model
'order_items__order__installation_requests'
```

### ❌ Incorrect: Skipping intermediate models
```python
# WRONG - Can't go directly from Product to Warranty (no direct relationship)
'warranty__warrantyclaim'

# CORRECT - Must go through SerializedItem
'serialized_items__warranty__claims'
```

### ❌ Incorrect: Using wrong related_name for reverse lookups
```python
# WRONG - 'warrantyclaim' is not the related_name
'warranty__warrantyclaim'

# CORRECT - 'claims' is the related_name defined in WarrantyClaim model
'warranty__claims'
```

### ❌ Incorrect: Wrong relationship path from WarrantyClaim to Product
```python
# WRONG - Warranty doesn't have a direct 'product' field
WarrantyClaim.objects.filter(warranty__product=product)

# CORRECT - Must go through SerializedItem
WarrantyClaim.objects.filter(warranty__serialized_item__product=product)
```

## Tips for Finding Correct Paths

1. **Check the model definition** for the `related_name` parameter in ForeignKey/OneToOne fields
2. **Follow the relationship chain** - ensure each step in the path exists
3. **Use distinct=True** when counting through many-to-many or reverse foreign key relationships to avoid duplicate counts
4. **Test in Django shell** before using in production code:
   ```python
   python manage.py shell
   >>> from products_and_services.models import Product
   >>> Product.objects.first().order_items.all()  # Test relationship exists
   ```

## Related Files
- **Models**: 
  - `products_and_services/models.py` (Product, SerializedItem, OrderItem)
  - `warranty/models.py` (Warranty, WarrantyClaim)
  - `customer_data/models.py` (Order, InstallationRequest)
- **View Fixed**: `admin_api/views.py` (AdminFaultAnalyticsViewSet)

## Issue History
- **Issue**: Django ORM annotation error in AdminFaultAnalyticsViewSet
- **Error Type**: `resolve_expression` failure during query annotation
- **Root Cause**: Incorrect relationship paths in Count() annotations
- **Fix Date**: 2026-01-22
- **Fixed By**: GitHub Copilot
