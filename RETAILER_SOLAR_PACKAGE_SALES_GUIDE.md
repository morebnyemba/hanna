# Retailer Solar Package Sales Interface - Implementation Guide

## Overview

This feature enables retailers to sell pre-configured solar system packages to customers through a dedicated portal interface. The implementation includes complete workflow automation from package selection through order creation, customer profile management, and installation request generation.

## Components

### Backend (Django)

#### Models (`products_and_services/models.py`)

1. **SolarPackage**
   - Stores pre-configured solar system packages
   - Fields: name, system_size, description, price, currency, is_active, compatibility_rules
   - Linked to products via many-to-many relationship

2. **SolarPackageProduct**
   - Through model for SolarPackage-Product relationship
   - Stores quantity of each product in a package

#### API Endpoints

All endpoints require authentication. Retailers can only access their own data.

**Base URL:** `/api/users/retailer/`

1. **List Solar Packages**
   - `GET /api/users/retailer/solar-packages/`
   - Returns all active solar packages with included products

2. **Get Solar Package Details**
   - `GET /api/users/retailer/solar-packages/{id}/`
   - Returns detailed information about a specific package

3. **Create Order**
   - `POST /api/users/retailer/orders/`
   - Creates complete order workflow (customer, order, installation request, SSR)
   
   **Request Body:**
   ```json
   {
     "solar_package_id": 1,
     "customer_first_name": "John",
     "customer_last_name": "Doe",
     "customer_phone": "+263771234567",
     "customer_email": "john@example.com",
     "customer_company": "Optional Company",
     "address_line_1": "123 Main St",
     "address_line_2": "Apt 4B",
     "city": "Harare",
     "state_province": "Harare",
     "postal_code": "00263",
     "country": "Zimbabwe",
     "latitude": -17.8252,
     "longitude": 31.0335,
     "payment_method": "paynow_ecocash",
     "loan_approved": false,
     "preferred_installation_date": "Next Monday",
     "installation_notes": "Please call before visiting"
   }
   ```

4. **List Orders**
   - `GET /api/users/retailer/orders/?page=1&page_size=10&stage=closed_won`
   - Returns paginated list of orders created by the retailer
   - Query params: page, page_size, stage

5. **Get Order Details**
   - `GET /api/users/retailer/orders/{uuid}/`
   - Returns detailed order information

### Frontend (React)

#### Pages

1. **RetailerSolarPackagesPage** (`/retailer/solar-packages`)
   - Displays grid of available solar packages
   - Shows package details: name, size, included products, price
   - "Create Order" button for each package

2. **RetailerCreateOrderPage** (`/retailer/orders/new?package={id}`)
   - Customer information form
   - Installation address form
   - Payment method selection
   - Installation preferences
   - Validates phone numbers and required fields

3. **RetailerOrdersPage** (`/retailer/orders`)
   - Lists all orders created by the retailer
   - Search and filter functionality
   - Pagination support
   - Status badges for order stage and payment status

## Setup Instructions

### 1. Database Migration

Run migrations to create the new models:

```bash
cd whatsappcrm_backend
python manage.py makemigrations products_and_services
python manage.py migrate
```

### 2. Create Solar Packages (Admin Interface)

1. Log into Django Admin: `http://your-domain/admin/`
2. Navigate to "Products and Services" → "Solar Packages"
3. Click "Add Solar Package"
4. Fill in package details:
   - Name (e.g., "3kW Starter System")
   - System Size (e.g., 3.0)
   - Description
   - Price
   - Mark as Active
5. Add products to the package using the inline form
6. Save the package

### 3. Configure Products

Ensure all products that will be included in packages have:
- Valid SKU
- Price set
- Active status
- Product type (hardware)

### 4. User Permissions

Retailers need the following:
- User account with `retailer_profile` or `retailer_branch_profile`
- Active retailer/branch status
- Authentication credentials

## Usage Workflow

### For Retailers

1. **Browse Packages**
   - Navigate to "Solar Packages" in the retailer portal
   - View all available solar system packages
   - Review package details, included products, and pricing

2. **Create Customer Order**
   - Click "Create Order" on desired package
   - Fill in customer details (name, phone, email)
   - Enter installation address
   - Select payment method
   - Add installation preferences
   - Submit order

3. **Track Orders**
   - View order history in "Order History" page
   - Search by order number or customer name
   - Filter by order status
   - Click on order to view details

### For Admins

1. **Create Solar Packages**
   - Design standard packages based on customer needs
   - Select appropriate products for each package
   - Set competitive pricing
   - Activate packages for retailer access

2. **Manage Products**
   - Keep product catalog up to date
   - Ensure accurate pricing
   - Maintain stock availability information

3. **Monitor Orders**
   - Review orders created by retailers
   - Assign technicians for installations
   - Track order fulfillment
   - Monitor payment status

## Order Workflow

When a retailer creates an order, the system automatically:

1. **Creates or Updates Contact**
   - Uses phone number as unique identifier
   - Creates WhatsApp contact record

2. **Creates or Updates CustomerProfile**
   - Links to contact
   - Stores customer details and address
   - Tracks lead status and acquisition source

3. **Creates Order**
   - Generates unique order number
   - Sets stage to "Closed Won"
   - Creates order items from package products
   - Calculates total amount
   - Records payment method
   - Attributes order to retailer

4. **Creates InstallationRequest**
   - Links to order and customer
   - Sets installation type to "solar"
   - Stores location data
   - Records installation preferences

5. **Creates InstallationSystemRecord (if available)**
   - Links to order and installation request
   - Sets system size from package
   - Initializes status as "pending"
   - Records installation address

6. **Sends Confirmation** (planned)
   - Notification to customer
   - Order confirmation details

## Testing

### Run Backend Tests

```bash
cd whatsappcrm_backend
python manage.py test products_and_services.test_solar_package
```

### Test API Endpoints

Use tools like Postman or curl:

```bash
# Get auth token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "retailer", "password": "password"}'

# List solar packages
curl http://localhost:8000/api/users/retailer/solar-packages/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Create order
curl -X POST http://localhost:8000/api/users/retailer/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d @order_data.json
```

### Test Frontend

1. Log in as a retailer user
2. Navigate to `/retailer/solar-packages`
3. Browse available packages
4. Click "Create Order" and fill in form
5. Submit order and verify success
6. Check `/retailer/orders` for order history

## Payment Methods

Available payment methods:
- **Paynow - Ecocash**: Mobile money (Ecocash)
- **Paynow - OneMoney**: Mobile money (OneMoney)
- **Paynow - Innbucks**: Mobile money (Innbucks)
- **Manual - Bank Transfer**: Direct bank transfer
- **Manual - Cash Payment**: Cash payment
- **Manual - Other**: Other payment methods

## Phone Number Format

Phone numbers must be in international format:
- Valid: `+263771234567`
- Valid: `+263 77 123 4567`
- Invalid: `0771234567` (missing country code)
- Invalid: `771234567` (missing prefix)

The system automatically normalizes phone numbers to E.164 format.

## Security Considerations

1. **Authentication Required**: All endpoints require valid JWT token
2. **Data Isolation**: Retailers can only access their own orders
3. **Phone Validation**: Phone numbers are validated and normalized
4. **Permission Checks**: IsRetailerOrAdmin permission class enforces access control
5. **Input Validation**: All user input is validated server-side

## Future Enhancements

Potential improvements for future releases:

1. **Compatibility Validation**
   - Validate product compatibility rules
   - Prevent incompatible product combinations
   - Auto-suggest compatible alternatives

2. **Credit Check Integration**
   - Integrate with loan approval systems
   - Auto-check customer credit eligibility
   - Link to loan application workflow

3. **Real-time Inventory**
   - Check product stock availability
   - Reserve products for orders
   - Auto-update inventory on order creation

4. **Enhanced Notifications**
   - WhatsApp notifications to customers
   - Email confirmations
   - SMS alerts for order updates

5. **Package Customization**
   - Allow retailers to customize packages
   - Add optional add-ons
   - Create custom quotes

6. **Commission Tracking**
   - Track retailer commissions
   - Auto-calculate earnings
   - Generate payout reports

## Troubleshooting

### Common Issues

1. **"Solar package not found or is not active"**
   - Ensure package is marked as active in admin
   - Verify package ID is correct

2. **"Invalid phone number format"**
   - Use international format with country code
   - Example: +263771234567

3. **"Cannot access endpoint"**
   - Verify user has retailer_profile or retailer_branch_profile
   - Check authentication token is valid
   - Ensure user account is active

4. **Order creation fails**
   - Check all required fields are provided
   - Verify payment method is valid
   - Ensure customer phone is in correct format
   - Check backend logs for detailed error

### Debug Mode

Enable debug logging in Django settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'customer_data': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Support

For issues or questions:
1. Check the logs: `docker-compose logs backend`
2. Review test cases for examples
3. Consult the API documentation
4. Contact the development team

## License

This feature is part of the HANNA CRM system and follows the project's license terms.
