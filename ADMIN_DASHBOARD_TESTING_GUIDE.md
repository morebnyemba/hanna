# Hanna Admin Dashboard Testing Guide

## Overview
This guide provides comprehensive testing instructions for the Hanna Management Frontend Admin Dashboard and its backend API endpoints.

## Prerequisites
- Admin user credentials (user must have `is_staff=True`)
- Access to the admin dashboard at https://hanna.co.zw/admin
- Backend API accessible at https://backend.hanna.co.zw

## Backend API Testing

### Authentication
All admin API endpoints require authentication with a staff/admin user:

```bash
# Get access token
curl -X POST https://backend.hanna.co.zw/crm-api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Use token in subsequent requests
curl -X GET https://backend.hanna.co.zw/crm-api/admin-panel/installation-requests/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Running Backend Tests

```bash
# Navigate to backend directory
cd whatsappcrm_backend

# Run all admin API tests
python manage.py test admin_api

# Run specific test class
python manage.py test admin_api.tests.AdminInstallationRequestAPITestCase

# Run with verbose output
python manage.py test admin_api --verbosity=2
```

### Test Coverage

The admin API test suite includes:
- ✅ Authentication and permission tests
- ✅ CRUD operations for all models
- ✅ Custom actions (mark_completed, approve, reject, assign_technicians)
- ✅ Filtering and search functionality
- ✅ Pagination support
- ✅ Error handling

## Frontend Testing

### Manual Testing Checklist

#### 1. Installation Requests Page (`/admin/installations`)
- [ ] **View**: List all installation requests
  - [ ] Verify status badges show correct colors
  - [ ] Verify technician names display correctly
  - [ ] Verify order numbers display when available
- [ ] **Filter**: Filter by status (pending, scheduled, in_progress, completed, cancelled)
  - [ ] Select each status filter and verify results
- [ ] **Search**: Search by customer name, address, order number, or technician
  - [ ] Enter various search terms and verify results
- [ ] **Select**: Click on an installation to view details in the right panel
  - [ ] Verify all details display correctly
  - [ ] Verify associated order items display if available
- [ ] **Mark Completed**: 
  - [ ] Click "Complete" button on a non-completed installation
  - [ ] Verify status changes to "Completed"
  - [ ] Verify button disappears after completion
  - [ ] Verify list refreshes automatically
- [ ] **Delete**: 
  - [ ] Click delete button
  - [ ] Verify confirmation modal appears
  - [ ] Cancel deletion and verify nothing changes
  - [ ] Confirm deletion and verify item removed from list

#### 2. Service Requests Page (`/admin/service-requests`)

##### Installation Requests Tab
- [ ] **View**: List all installation requests
- [ ] **Mark Completed**: 
  - [ ] Click "Complete" button on pending/in_progress installations
  - [ ] Verify status updates correctly
  - [ ] Verify button only shows for non-completed requests
- [ ] **Delete**: 
  - [ ] Delete an installation request with confirmation
  - [ ] Verify removal from list

##### Site Assessments Tab
- [ ] **View**: List all site assessment requests
  - [ ] Verify assessment type displays correctly
- [ ] **Mark Assessed**: 
  - [ ] Click "Mark Assessed" button on pending assessments
  - [ ] Verify status changes to "assessed"
  - [ ] Verify button disappears after marking
- [ ] **Delete**: Delete a site assessment with confirmation

##### Loan Applications Tab
- [ ] **View**: List all loan applications
  - [ ] Verify loan type and amount display correctly
- [ ] **Approve**: 
  - [ ] Click "Approve" button on pending loans
  - [ ] Verify status changes to "approved"
  - [ ] Verify approve/reject buttons disappear
- [ ] **Reject**: 
  - [ ] Click "Reject" button on pending loans
  - [ ] Verify status changes to "rejected"
  - [ ] Verify approve/reject buttons disappear
- [ ] **Delete**: Delete a loan application with confirmation

#### 3. Products Page (`/admin/products`)
- [ ] **View**: List all products
- [ ] **Create**: Create a new product
- [ ] **Edit**: Edit an existing product
- [ ] **Delete**: Delete a product with confirmation

#### 4. Product Categories Page (`/admin/product-categories`)
- [ ] **View**: List all categories
- [ ] **Create**: Create a new category
- [ ] **Edit**: Edit an existing category
- [ ] **Delete**: Delete a category with confirmation

#### 5. Serialized Items Page (`/admin/serialized-items`)
- [ ] **View**: List all serialized items
- [ ] **Create**: Create a new serialized item
- [ ] **View Details**: View details of a serialized item
- [ ] **Delete**: Delete a serialized item with confirmation

#### 6. Customers Page (`/admin/customers`)
- [ ] **View**: List all customers
- [ ] **Create**: Add a new customer
- [ ] **View Details**: View customer profile details
- [ ] **Delete**: Delete a customer with confirmation

#### 7. Flows Page (`/admin/flows`)
- [ ] **View**: List all WhatsApp flows
- [ ] **Create**: Create a new flow
- [ ] **Delete**: Delete a flow with confirmation

#### 8. Warranty Claims Page (`/admin/warranty-claims`)
- [ ] **View**: List all warranty claims
- [ ] **Create**: Create a new warranty claim
- [ ] **Delete**: Delete a warranty claim with confirmation

#### 9. Orders Page (`/admin/orders`)
- [ ] **View**: List all orders
- [ ] **Filter**: Filter orders by status
- [ ] **Search**: Search orders by customer or order number
- [ ] **View Details**: View order details

#### 10. Users Page (`/admin/users`)
- [ ] **View**: List all users
- [ ] **Invite**: Send user invitation
- [ ] **Manage Roles**: Update user permissions

#### 11. Dashboard Page (`/admin/dashboard`)
- [ ] **View**: Analytics and charts display correctly
- [ ] **Stats**: Summary statistics show accurate numbers
- [ ] **Activity Log**: Recent activities display

#### 12. Settings Page (`/admin/settings`)
- [ ] **View**: Settings page loads without errors
- [ ] **Update**: Settings can be updated if applicable

## API Endpoint Testing

### Installation Requests API

```bash
# List all installations
GET /crm-api/admin-panel/installation-requests/

# Filter by status
GET /crm-api/admin-panel/installation-requests/?status=pending

# Search by name
GET /crm-api/admin-panel/installation-requests/?search=John

# Get specific installation
GET /crm-api/admin-panel/installation-requests/{id}/

# Create installation
POST /crm-api/admin-panel/installation-requests/
{
  "customer": 1,
  "status": "pending",
  "installation_type": "solar",
  "full_name": "John Doe",
  "address": "123 Main St",
  "contact_phone": "+1234567890",
  "preferred_datetime": "2024-01-15 10:00"
}

# Update installation
PUT /crm-api/admin-panel/installation-requests/{id}/
PATCH /crm-api/admin-panel/installation-requests/{id}/

# Delete installation
DELETE /crm-api/admin-panel/installation-requests/{id}/

# Mark as completed
POST /crm-api/admin-panel/installation-requests/{id}/mark_completed/

# Assign technicians
POST /crm-api/admin-panel/installation-requests/{id}/assign_technicians/
{
  "technician_ids": [1, 2, 3]
}
```

### Site Assessment Requests API

```bash
# List all assessments
GET /crm-api/admin-panel/site-assessment-requests/

# Filter by status
GET /crm-api/admin-panel/site-assessment-requests/?status=pending

# Create assessment
POST /crm-api/admin-panel/site-assessment-requests/

# Mark as assessed
POST /crm-api/admin-panel/site-assessment-requests/{id}/mark_completed/

# Delete assessment
DELETE /crm-api/admin-panel/site-assessment-requests/{id}/
```

### Loan Applications API

```bash
# List all loans
GET /crm-api/admin-panel/loan-applications/

# Filter by status
GET /crm-api/admin-panel/loan-applications/?status=pending

# Create loan application
POST /crm-api/admin-panel/loan-applications/

# Approve loan
POST /crm-api/admin-panel/loan-applications/{id}/approve/

# Reject loan
POST /crm-api/admin-panel/loan-applications/{id}/reject/

# Delete loan application
DELETE /crm-api/admin-panel/loan-applications/{id}/
```

## Error Scenarios to Test

### Authentication Errors
- [ ] Test endpoints without authentication token (should return 401)
- [ ] Test endpoints with non-staff user (should return 403)
- [ ] Test endpoints with expired token (should return 401)

### Validation Errors
- [ ] Try to create installation without required fields (should return 400)
- [ ] Try to assign non-existent technician (should return 400)
- [ ] Try to mark non-existent installation as completed (should return 404)

### Edge Cases
- [ ] Test with very long text in fields
- [ ] Test with special characters in search
- [ ] Test pagination with large datasets
- [ ] Test concurrent updates to same record
- [ ] Test delete of record with foreign key relationships

## Performance Testing

### Load Testing
```bash
# Use Apache Bench for basic load testing
ab -n 1000 -c 10 -H "Authorization: Bearer TOKEN" \
  https://backend.hanna.co.zw/crm-api/admin-panel/installation-requests/

# Expected: < 500ms response time for list endpoints
# Expected: < 200ms response time for detail endpoints
```

### Database Queries
- [ ] Monitor database query count using Django Debug Toolbar
- [ ] Verify select_related/prefetch_related are used appropriately
- [ ] Check for N+1 query problems

## Security Testing

### Access Control
- [ ] Verify non-admin users cannot access admin endpoints
- [ ] Verify unauthenticated users get 401 errors
- [ ] Verify CSRF protection is enabled
- [ ] Verify XSS protection in frontend

### Data Validation
- [ ] Test SQL injection attempts in search fields
- [ ] Test XSS attempts in text fields
- [ ] Verify file upload restrictions if applicable

## Browser Compatibility

Test the frontend on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile browsers (iOS Safari, Chrome Android)

## Responsive Design

Test on different screen sizes:
- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

## Known Issues

Document any known issues here:
- None currently reported

## Reporting Bugs

When reporting bugs, include:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Browser/environment information
5. Screenshots if applicable
6. Error messages from console

## Continuous Integration

### GitHub Actions (if configured)
- Backend tests run on every push
- Frontend build verification on every push
- Deployment to staging on merge to main

## Accessibility Testing

- [ ] Test with screen reader (NVDA/JAWS)
- [ ] Test keyboard navigation
- [ ] Verify ARIA labels are present
- [ ] Check color contrast ratios
- [ ] Verify focus indicators are visible

## Conclusion

This testing guide should be updated as new features are added. All team members should be familiar with this guide and use it for manual testing before releases.
