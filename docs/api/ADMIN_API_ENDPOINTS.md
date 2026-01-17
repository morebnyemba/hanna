# Admin API Endpoints Documentation

## Base URL
All admin API endpoints are prefixed with `/crm-api/admin-panel/`

## Authentication
All endpoints require JWT authentication with a staff user (`is_staff=True`).

### Getting Access Token
```bash
POST /crm-api/auth/token/
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using Token
Include the access token in the Authorization header:
```
Authorization: Bearer <access_token>
```

## Common Response Formats

### Paginated List Response
```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### Error Response
```json
{
  "detail": "Error message"
}
```

## Installation Requests

### List Installation Requests
```
GET /crm-api/admin-panel/installation-requests/
```

**Query Parameters:**
- `status` - Filter by status (pending, scheduled, in_progress, completed, cancelled)
- `installation_type` - Filter by type (starlink, solar, hybrid, custom_furniture, residential, commercial)
- `customer` - Filter by customer ID
- `search` - Search in order_number, full_name, address, contact_phone
- `ordering` - Order by field (e.g., `-created_at`, `status`)
- `page` - Page number for pagination
- `page_size` - Results per page (default: 100)

**Response:**
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "customer": {...},
      "customer_full_name": "John Doe",
      "associated_order": {...},
      "status": "pending",
      "status_display": "Pending",
      "installation_type": "solar",
      "installation_type_display": "Solar Panel Installation",
      "order_number": "ORD-001",
      "full_name": "John Doe",
      "address": "123 Main St, Harare",
      "contact_phone": "+263712345678",
      "preferred_datetime": "2024-01-15 10:00",
      "technicians": [...],
      "notes": "Customer requested morning appointment",
      "created_at": "2024-01-10T08:30:00Z",
      "updated_at": "2024-01-10T08:30:00Z"
    }
  ]
}
```

### Get Installation Request
```
GET /crm-api/admin-panel/installation-requests/{id}/
```

### Create Installation Request
```
POST /crm-api/admin-panel/installation-requests/
Content-Type: application/json

{
  "customer": 1,
  "status": "pending",
  "installation_type": "solar",
  "full_name": "John Doe",
  "address": "123 Main St",
  "contact_phone": "+263712345678",
  "preferred_datetime": "2024-01-15 10:00",
  "notes": "Optional notes"
}
```

### Update Installation Request
```
PUT /crm-api/admin-panel/installation-requests/{id}/
PATCH /crm-api/admin-panel/installation-requests/{id}/
```

### Delete Installation Request
```
DELETE /crm-api/admin-panel/installation-requests/{id}/
```

### Mark Installation as Completed
```
POST /crm-api/admin-panel/installation-requests/{id}/mark_completed/

Response:
{
  "message": "Installation marked as completed successfully.",
  "data": {...}
}
```

### Assign Technicians
```
POST /crm-api/admin-panel/installation-requests/{id}/assign_technicians/
Content-Type: application/json

{
  "technician_ids": [1, 2, 3]
}

Response:
{
  "message": "Successfully assigned 3 technician(s).",
  "data": {...}
}
```

## Site Assessment Requests

### List Site Assessments
```
GET /crm-api/admin-panel/site-assessment-requests/
```

**Query Parameters:**
- `status` - Filter by status (pending, scheduled, assessed, cancelled)
- `assessment_type` - Filter by type (starlink, commercial_solar, hybrid_starlink_solar, custom_furniture, other)
- `customer` - Filter by customer ID
- `search` - Search in assessment_id, full_name, address, contact_info
- `ordering` - Order by field
- `page`, `page_size` - Pagination

**Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "assessment_id": "ASM-001",
      "customer": {...},
      "customer_full_name": "Jane Smith",
      "status": "pending",
      "status_display": "Pending",
      "assessment_type": "commercial_solar",
      "assessment_type_display": "Commercial Solar System",
      "full_name": "Jane Smith",
      "company_name": "ABC Corp",
      "address": "456 Business St",
      "contact_info": "+263712345679",
      "preferred_day": "Monday",
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-01-10T09:00:00Z"
    }
  ]
}
```

### Create Site Assessment
```
POST /crm-api/admin-panel/site-assessment-requests/
```

### Mark Assessment as Completed
```
POST /crm-api/admin-panel/site-assessment-requests/{id}/mark_completed/

Response:
{
  "message": "Site assessment marked as assessed successfully.",
  "data": {...}
}
```

### Delete Site Assessment
```
DELETE /crm-api/admin-panel/site-assessment-requests/{id}/
```

## Loan Applications

### List Loan Applications
```
GET /crm-api/admin-panel/loan-applications/
```

**Query Parameters:**
- `status` - Filter by status (pending, approved, rejected, cancelled)
- `loan_type` - Filter by type
- `customer` - Filter by customer ID
- `search` - Search in application_id, full_name, national_id, notes
- `ordering` - Order by field
- `page`, `page_size` - Pagination

**Response:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "application_id": "LOAN-001",
      "customer": {...},
      "customer_full_name": "Alice Johnson",
      "status": "pending",
      "status_display": "Pending",
      "loan_type": "solar_financing",
      "loan_type_display": "Solar Financing",
      "full_name": "Alice Johnson",
      "national_id": "12-345678A12",
      "requested_amount": "15000.00",
      "notes": "",
      "created_at": "2024-01-10T10:00:00Z",
      "updated_at": "2024-01-10T10:00:00Z"
    }
  ]
}
```

### Create Loan Application
```
POST /crm-api/admin-panel/loan-applications/
```

### Approve Loan Application
```
POST /crm-api/admin-panel/loan-applications/{id}/approve/

Response:
{
  "message": "Loan application approved successfully.",
  "data": {...}
}
```

### Reject Loan Application
```
POST /crm-api/admin-panel/loan-applications/{id}/reject/

Response:
{
  "message": "Loan application rejected.",
  "data": {...}
}
```

### Delete Loan Application
```
DELETE /crm-api/admin-panel/loan-applications/{id}/
```

## Users

### List Users
```
GET /crm-api/admin-panel/users/
```

**Query Parameters:**
- `is_active` - Filter by active status
- `is_staff` - Filter by staff status
- `is_superuser` - Filter by superuser status
- `search` - Search in username, email, first_name, last_name
- `ordering` - Order by field (username, email, date_joined, last_login)

### Get User
```
GET /crm-api/admin-panel/users/{id}/
```

### Create User
```
POST /crm-api/admin-panel/users/
```

### Update User
```
PUT /crm-api/admin-panel/users/{id}/
PATCH /crm-api/admin-panel/users/{id}/
```

### Delete User
```
DELETE /crm-api/admin-panel/users/{id}/
```

## Notifications

### List Notifications
```
GET /crm-api/admin-panel/notifications/
```

**Query Parameters:**
- `status` - Filter by status
- `channel` - Filter by channel (email, whatsapp, sms)
- `recipient` - Filter by recipient ID
- `search` - Search in recipient username/email

### Notification Templates
```
GET /crm-api/admin-panel/notification-templates/
POST /crm-api/admin-panel/notification-templates/
GET /crm-api/admin-panel/notification-templates/{id}/
PUT /crm-api/admin-panel/notification-templates/{id}/
DELETE /crm-api/admin-panel/notification-templates/{id}/
```

## AI Providers

### List AI Providers
```
GET /crm-api/admin-panel/ai-providers/
```

**Query Parameters:**
- `provider` - Filter by provider name
- `is_active` - Filter by active status

### Manage AI Providers
```
POST /crm-api/admin-panel/ai-providers/
GET /crm-api/admin-panel/ai-providers/{id}/
PUT /crm-api/admin-panel/ai-providers/{id}/
DELETE /crm-api/admin-panel/ai-providers/{id}/
```

## Email Integration

### SMTP Configs
```
GET /crm-api/admin-panel/smtp-configs/
POST /crm-api/admin-panel/smtp-configs/
GET /crm-api/admin-panel/smtp-configs/{id}/
PUT /crm-api/admin-panel/smtp-configs/{id}/
DELETE /crm-api/admin-panel/smtp-configs/{id}/
```

### Email Accounts
```
GET /crm-api/admin-panel/email-accounts/
POST /crm-api/admin-panel/email-accounts/
GET /crm-api/admin-panel/email-accounts/{id}/
PUT /crm-api/admin-panel/email-accounts/{id}/
DELETE /crm-api/admin-panel/email-accounts/{id}/
```

### Email Attachments (Read-only)
```
GET /crm-api/admin-panel/email-attachments/
GET /crm-api/admin-panel/email-attachments/{id}/
```

**Query Parameters:**
- `processed` - Filter by processed status
- `search` - Search in filename, sender

### Parsed Invoices (Read-only)
```
GET /crm-api/admin-panel/parsed-invoices/
GET /crm-api/admin-panel/parsed-invoices/{id}/
```

### Admin Email Recipients
```
GET /crm-api/admin-panel/admin-email-recipients/
POST /crm-api/admin-panel/admin-email-recipients/
GET /crm-api/admin-panel/admin-email-recipients/{id}/
PUT /crm-api/admin-panel/admin-email-recipients/{id}/
DELETE /crm-api/admin-panel/admin-email-recipients/{id}/
```

## Retailers

### List Retailers
```
GET /crm-api/admin-panel/retailers/
```

**Query Parameters:**
- `is_active` - Filter by active status
- `search` - Search in company_name, contact_phone, contact_email

### Manage Retailers
```
POST /crm-api/admin-panel/retailers/
GET /crm-api/admin-panel/retailers/{id}/
PUT /crm-api/admin-panel/retailers/{id}/
DELETE /crm-api/admin-panel/retailers/{id}/
```

### Retailer Branches
```
GET /crm-api/admin-panel/retailer-branches/
POST /crm-api/admin-panel/retailer-branches/
GET /crm-api/admin-panel/retailer-branches/{id}/
PUT /crm-api/admin-panel/retailer-branches/{id}/
DELETE /crm-api/admin-panel/retailer-branches/{id}/
```

**Query Parameters:**
- `is_active` - Filter by active status
- `retailer` - Filter by retailer ID
- `search` - Search in branch_name, branch_code, contact_phone

## Warranty Management

### Manufacturers
```
GET /crm-api/admin-panel/manufacturers/
POST /crm-api/admin-panel/manufacturers/
GET /crm-api/admin-panel/manufacturers/{id}/
PUT /crm-api/admin-panel/manufacturers/{id}/
DELETE /crm-api/admin-panel/manufacturers/{id}/
```

### Technicians
```
GET /crm-api/admin-panel/technicians/
POST /crm-api/admin-panel/technicians/
GET /crm-api/admin-panel/technicians/{id}/
PUT /crm-api/admin-panel/technicians/{id}/
DELETE /crm-api/admin-panel/technicians/{id}/
```

### Warranties
```
GET /crm-api/admin-panel/warranties/
POST /crm-api/admin-panel/warranties/
GET /crm-api/admin-panel/warranties/{id}/
PUT /crm-api/admin-panel/warranties/{id}/
DELETE /crm-api/admin-panel/warranties/{id}/
```

**Query Parameters:**
- `status` - Filter by status
- `manufacturer` - Filter by manufacturer ID
- `search` - Search in serial number, customer name

### Warranty Claims
```
GET /crm-api/admin-panel/warranty-claims/
POST /crm-api/admin-panel/warranty-claims/
GET /crm-api/admin-panel/warranty-claims/{id}/
PUT /crm-api/admin-panel/warranty-claims/{id}/
DELETE /crm-api/admin-panel/warranty-claims/{id}/
```

**Query Parameters:**
- `status` - Filter by status
- `search` - Search in claim_id, serial number

## Stats

### Daily Stats (Read-only)
```
GET /crm-api/admin-panel/daily-stats/
GET /crm-api/admin-panel/daily-stats/{id}/
```

**Query Parameters:**
- `date` - Filter by specific date
- `ordering` - Order by date

## Cart Management

### Carts
```
GET /crm-api/admin-panel/carts/
POST /crm-api/admin-panel/carts/
GET /crm-api/admin-panel/carts/{id}/
PUT /crm-api/admin-panel/carts/{id}/
DELETE /crm-api/admin-panel/carts/{id}/
```

**Query Parameters:**
- `contact` - Filter by contact ID
- `search` - Search in contact name, whatsapp_id

### Cart Items
```
GET /crm-api/admin-panel/cart-items/
POST /crm-api/admin-panel/cart-items/
GET /crm-api/admin-panel/cart-items/{id}/
PUT /crm-api/admin-panel/cart-items/{id}/
DELETE /crm-api/admin-panel/cart-items/{id}/
```

**Query Parameters:**
- `cart` - Filter by cart ID

## Permissions

All endpoints require:
- User must be authenticated
- User must have `is_staff=True`

Non-admin users will receive:
```json
{
  "detail": "You do not have permission to perform this action."
}
```

## Rate Limiting

Currently no rate limiting is implemented, but it's recommended to:
- Limit API requests to 1000 per hour per user
- Implement exponential backoff for failed requests
- Cache frequently accessed data on the frontend

## Best Practices

1. **Always use pagination** for list endpoints with large datasets
2. **Use search and filtering** to reduce payload size
3. **Cache responses** on the frontend when appropriate
4. **Handle errors gracefully** and show user-friendly messages
5. **Use PATCH** for partial updates instead of PUT
6. **Include meaningful search terms** to get relevant results
7. **Order results** by relevant fields (e.g., `-created_at` for most recent first)

## Error Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `500 Internal Server Error` - Server error

## Support

For API issues or questions:
1. Check Django logs: `docker-compose logs backend`
2. Check Nginx logs: `docker-compose logs nginx`
3. Verify authentication token is valid
4. Ensure user has staff permissions
5. Open an issue on GitHub with error details
