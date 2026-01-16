# Installer Payout System - API Reference

## Base URLs

- Admin API: `/api/admin/`
- Installation Systems API: `/api/installation-systems/`

## Authentication

All endpoints require authentication. Admin endpoints require admin/staff permissions.

```bash
# Include authentication header
Authorization: Token <your-auth-token>
# or
Authorization: Bearer <your-jwt-token>
```

---

## Payout Configuration Endpoints

### List Payout Configurations

**GET** `/api/admin/payout-configurations/`

**Query Parameters:**
- `installation_type`: Filter by installation type (solar, starlink, hybrid, custom_furniture)
- `is_active`: Filter by active status (true/false)
- `rate_type`: Filter by rate type (flat, per_unit, percentage)
- `search`: Search in name field
- `ordering`: Sort by field (priority, name, created_at)

**Response:**
```json
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "name": "Solar Standard Rate",
      "installation_type": "solar",
      "installation_type_display": "Solar Panel Installation",
      "min_system_size": "0.00",
      "max_system_size": "10.00",
      "capacity_unit": "kW",
      "capacity_unit_display": "Kilowatts (kW)",
      "rate_type": "per_unit",
      "rate_type_display": "Per Unit Rate",
      "rate_amount": "50.00",
      "quality_bonus_enabled": false,
      "quality_bonus_amount": null,
      "is_active": true,
      "priority": 1,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Create Payout Configuration

**POST** `/api/admin/payout-configurations/`

**Request Body:**
```json
{
  "name": "Solar Standard Rate",
  "installation_type": "solar",
  "min_system_size": "0.00",
  "max_system_size": "10.00",
  "capacity_unit": "kW",
  "rate_type": "per_unit",
  "rate_amount": "50.00",
  "quality_bonus_enabled": false,
  "is_active": true,
  "priority": 1
}
```

**Response:** 201 Created (same structure as GET)

### Get Active Configurations

**GET** `/api/admin/payout-configurations/active/`

Returns only configurations where `is_active=true`.

---

## Installer Payout Endpoints

### List Payouts

**GET** `/api/admin/installer-payouts/`

**Query Parameters:**
- `technician`: Filter by technician ID
- `status`: Filter by status (pending, approved, rejected, paid)
- `approved_by`: Filter by approver user ID
- `search`: Search in technician name, payment reference, notes
- `ordering`: Sort by field (created_at, payout_amount, approved_at, paid_at)

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": "uuid",
      "short_id": "PAY-abc12345",
      "technician": 123,
      "technician_name": "John Doe",
      "installation_count": 3,
      "payout_amount": "750.00",
      "status": "pending",
      "status_display": "Pending",
      "approved_by": null,
      "approved_by_name": null,
      "approved_at": null,
      "paid_at": null,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Get Payout Details

**GET** `/api/admin/installer-payouts/{id}/`

**Response:**
```json
{
  "id": "uuid",
  "short_id": "PAY-abc12345",
  "technician": 123,
  "technician_details": {
    "id": 123,
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+263771234567",
    "specialization": "Solar",
    "technician_type": "installer",
    "technician_type_display": "Installer"
  },
  "installations": ["uuid1", "uuid2", "uuid3"],
  "installation_details": [
    {
      "id": "uuid1",
      "short_id": "ISR-12345678",
      "customer_name": "Jane Smith",
      "installation_type": "solar",
      "installation_type_display": "Solar Panel Installation",
      "system_size": "5.00",
      "capacity_unit": "kW",
      "installation_status": "commissioned",
      "installation_status_display": "Commissioned",
      "installation_date": "2024-01-10",
      "commissioning_date": "2024-01-12",
      "order_number": "ORD-001"
    }
  ],
  "configuration": "uuid",
  "configuration_details": {
    "id": "uuid",
    "name": "Solar Standard Rate",
    "installation_type": "solar",
    "rate_type": "per_unit",
    "rate_type_display": "Per Unit Rate",
    "rate_amount": "50.00",
    "min_system_size": "0.00",
    "max_system_size": "10.00",
    "capacity_unit": "kW"
  },
  "payout_amount": "750.00",
  "calculation_method": "Total payout for 3 installations:\n- ISR-12345678: Per unit rate: $50.00 × 5.0kW = $250.00\n...\n\nTotal: $750.00",
  "calculation_breakdown": {
    "technician_id": 123,
    "technician_name": "John Doe",
    "installation_count": 3,
    "installations": [...],
    "total_amount": "750.00"
  },
  "status": "pending",
  "status_display": "Pending",
  "notes": "Monthly payout",
  "admin_notes": "",
  "rejection_reason": "",
  "approved_by": null,
  "approval_details": null,
  "approved_at": null,
  "paid_at": null,
  "payment_reference": "",
  "zoho_details": {
    "bill_id": "",
    "sync_status": "",
    "sync_error": "",
    "synced_at": null
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Create Payout

**POST** `/api/admin/installer-payouts/`

**Request Body:**
```json
{
  "technician": 123,
  "installations": ["uuid1", "uuid2", "uuid3"],
  "notes": "Monthly payout for January"
}
```

The system will automatically:
- Calculate the payout amount based on configurations
- Generate calculation method and breakdown
- Set status to PENDING
- Find matching payout configurations for each installation

**Response:** 201 Created (full payout details)

### Approve/Reject Payout

**POST** `/api/admin/installer-payouts/{id}/approve/`

**Request Body (Approve):**
```json
{
  "action": "approve",
  "admin_notes": "All installations verified and completed"
}
```

**Request Body (Reject):**
```json
{
  "action": "reject",
  "rejection_reason": "Missing commissioning certificates for ISR-12345678",
  "admin_notes": "Need to resubmit with proper documentation"
}
```

**Response:**
```json
{
  "message": "Payout approved successfully",
  "payout": {
    // Full payout details
  }
}
```

**Side Effects:**
- **On Approve:** 
  - Status changed to APPROVED
  - Triggers Zoho sync (if configured)
  - Sends approval email to technician
- **On Reject:**
  - Status changed to REJECTED
  - Sends rejection email to technician

### Mark as Paid

**POST** `/api/admin/installer-payouts/{id}/mark_paid/`

**Request Body:**
```json
{
  "payment_reference": "TXN-2024-001234",
  "payment_date": "2024-01-16T10:30:00Z",
  "notes": "Paid via bank transfer to account ending in 1234"
}
```

**Response:**
```json
{
  "message": "Payout marked as paid successfully",
  "payout": {
    // Full payout details
  }
}
```

**Side Effects:**
- Status changed to PAID
- Sends payment confirmation email to technician

### Sync to Zoho

**POST** `/api/admin/installer-payouts/{id}/sync_to_zoho/`

**Response:**
```json
{
  "message": "Zoho sync queued successfully",
  "task_id": "celery-task-id"
}
```

### Get Pending Payouts

**GET** `/api/admin/installer-payouts/pending/`

Returns only payouts with status=PENDING.

### Get Payout History

**GET** `/api/admin/installer-payouts/history/`

Returns payouts with status=APPROVED, REJECTED, or PAID.

### Get Payouts by Technician

**GET** `/api/admin/installer-payouts/by_technician/`

**Query Parameters:**
- `status`: Filter by status (optional)

**Response:**
```json
[
  {
    "technician": 123,
    "technician__user__first_name": "John",
    "technician__user__last_name": "Doe",
    "technician__user__email": "john@example.com",
    "total_payouts": 5,
    "total_amount": "2500.00"
  }
]
```

---

## Technician-Facing Endpoints

Technicians can view their own payouts (read-only):

**GET** `/api/installation-systems/installer-payouts/`

Returns only payouts for the authenticated technician.

**GET** `/api/installation-systems/installer-payouts/{id}/`

Returns payout details only if it belongs to the authenticated technician.

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Cannot approve payout with status Paid",
  "field_name": ["Error message for specific field"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to queue Zoho sync: connection timeout"
}
```

---

## Status Flow

```
PENDING → APPROVED → PAID
    ↓
REJECTED
```

- **PENDING**: Initial state, awaiting admin review
- **APPROVED**: Admin approved, ready for payment
- **REJECTED**: Admin rejected, needs revision
- **PAID**: Payment completed

---

## Rate Types

### Flat Rate
Fixed amount regardless of system size.

**Example:**
```json
{
  "rate_type": "flat",
  "rate_amount": "100.00"
}
```
Every installation pays $100.

### Per Unit Rate
Amount multiplied by system size.

**Example:**
```json
{
  "rate_type": "per_unit",
  "rate_amount": "50.00"
}
```
5kW system pays $250 (5 × $50).

### Percentage
Percentage of order total (future enhancement).

**Example:**
```json
{
  "rate_type": "percentage",
  "rate_amount": "10.00"
}
```
$1000 order pays $100 (10% of $1000).

---

## Testing Examples

### Create Test Payout Configuration
```bash
curl -X POST http://localhost:8000/api/admin/payout-configurations/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Solar Rate",
    "installation_type": "solar",
    "capacity_unit": "kW",
    "rate_type": "per_unit",
    "rate_amount": "45.00",
    "is_active": true,
    "priority": 1
  }'
```

### List Pending Payouts
```bash
curl -X GET http://localhost:8000/api/admin/installer-payouts/pending/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Approve Payout
```bash
curl -X POST http://localhost:8000/api/admin/installer-payouts/{id}/approve/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "approve",
    "admin_notes": "Verified all installations"
  }'
```

### Mark as Paid
```bash
curl -X POST http://localhost:8000/api/admin/installer-payouts/{id}/mark_paid/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_reference": "TXN-001",
    "payment_date": "2024-01-16T10:30:00Z"
  }'
```
