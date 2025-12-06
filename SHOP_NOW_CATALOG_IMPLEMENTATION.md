# Shop Now Catalog and Cart Processing Implementation

## Overview

This document describes the complete implementation of the WhatsApp catalog shopping experience with order processing and payment initiation.

## Implementation Status: ✅ COMPLETE

All three requested features are fully implemented:

1. ✅ **Shop Now option opens the catalog**
2. ✅ **Process cart sent by a user**
3. ✅ **Send payment initiation WhatsApp flow with endpoint**

## Architecture

### 1. Shop Now Opens Catalog

**Location**: `whatsappcrm_backend/flows/definitions/main_menu_flow.py`

When a user selects "🛒 Shop Products" from the main menu, the flow executes the `switch_to_purchase_flow` step:

```python
{
    "name": "switch_to_purchase_flow",
    "type": "action",
    "config": {
        "actions_to_run": [
            {
                "action_type": "send_catalog_message",
                "params_template": {
                    "header_text": "🛒 Pfungwa Product Catalog",
                    "body_text": "Browse our products below and add items to your cart...",
                    "footer_text": "Tap on products to view details"
                }
            }
        ]
    }
}
```

**Action Implementation**: `whatsappcrm_backend/flows/actions.py::send_catalog_message()`

This action:
- Retrieves the active MetaAppConfig and catalog_id
- Builds an interactive catalog message payload conforming to WhatsApp's API
- Returns the message to be sent via the Meta API
- Allows users to browse products and add them to cart directly in WhatsApp

### 2. Process Cart Order

**Webhook Handler**: `whatsappcrm_backend/meta_integration/views.py::_handle_message()`

When a user submits their cart from WhatsApp catalog:
- The webhook receives a message of type "order"
- The handler calls `_handle_order_message()`
- Which delegates to `process_order_from_catalog()` in flows/services.py

**Order Processing**: `whatsappcrm_backend/flows/services.py::process_order_from_catalog()`

This function:
1. Parses the order data from the WhatsApp message
2. Extracts product items with SKUs, quantities, and prices
3. Creates or gets CustomerProfile for the contact
4. Generates a unique order number (format: `WA-XXXXX`)
5. Calculates the total amount from all items
6. Creates an Order record with:
   - Customer profile link
   - Order number
   - Stage: CLOSED_WON
   - Payment Status: PENDING
   - Amount and currency
   - Notes with catalog ID and customer message
7. Creates OrderItem records for each product in the cart
8. Sends a confirmation message to the user
9. Initiates the payment flow (if available)

**Alternative Action**: `whatsappcrm_backend/flows/actions.py::process_cart_order()`

This is a flow action that can be called from within conversational flows to process cart data stored in context. It performs similar operations to `process_order_from_catalog()` but works with cart data from the flow context rather than directly from webhook messages.

### 3. Payment Initiation Flow with Endpoint

**Flow Action**: `whatsappcrm_backend/flows/actions.py::initiate_payment_flow()`

This action:
1. Retrieves order data from context
2. Finds the published WhatsApp payment flow
3. Builds an interactive flow message with:
   - Header: "Complete Your Payment"
   - Body: Order details and amount
   - Flow parameters including order number, amount, currency
   - Flow action payload with payment screen data
4. Sends the interactive flow message to the user

**Payment Endpoint**: `whatsappcrm_backend/paynow_integration/views.py::initiate_whatsapp_payment()`

URL: `/api/crm-api/paynow/initiate-payment/`

This endpoint:
- Accepts payment details from WhatsApp flow (order_number, phone_number, amount, payment_method)
- Validates required fields
- Finds the associated Order
- Creates a Payment record
- Initiates Paynow express checkout
- Returns payment details and instructions
- Updates order payment status

**Payment Callback**: `whatsappcrm_backend/paynow_integration/views.py::paynow_ipn_handler()`

URL: `/api/crm-api/paynow/ipn/`

This IPN (Instant Payment Notification) handler:
- Receives payment status updates from Paynow
- Verifies the payment hash
- Updates Payment record status
- Updates Order payment status when successful
- Sends WhatsApp confirmation message to customer

## Flow Diagram

```
User Interaction Flow:
======================

1. User: Sends "menu" or "hi"
   ↓
2. System: Shows main menu with "🛒 Shop Products" option
   ↓
3. User: Selects "Shop Products"
   ↓
4. System: Sends WhatsApp catalog message (send_catalog_message)
   ↓
5. User: Browses catalog, adds items to cart, submits order
   ↓
6. WhatsApp: Sends order message to webhook
   ↓
7. System: Processes order (process_order_from_catalog)
   - Creates Order record
   - Creates OrderItem records
   - Sends confirmation message
   ↓
8. System: Initiates payment flow (from process_order_from_catalog or via initiate_payment_flow action)
   - Sends WhatsApp Flow with payment form
   ↓
9. User: Fills payment form in WhatsApp Flow
   ↓
10. WhatsApp Flow: Sends data to payment endpoint
    ↓
11. System: Processes payment (initiate_whatsapp_payment)
    - Creates Payment record
    - Initiates Paynow transaction
    - Returns instructions to user
    ↓
12. Paynow: Sends IPN callback when payment completes
    ↓
13. System: Updates payment and order status (paynow_ipn_handler)
    - Sends confirmation to user via WhatsApp
```

## Key Files

### Flow Definitions
- `whatsappcrm_backend/flows/definitions/main_menu_flow.py` - Main menu with Shop Products option

### Actions
- `whatsappcrm_backend/flows/actions.py`:
  - `send_catalog_message()` - Sends catalog to user
  - `process_cart_order()` - Processes cart from context
  - `initiate_payment_flow()` - Sends payment flow message

### Services
- `whatsappcrm_backend/flows/services.py`:
  - `process_order_from_catalog()` - Processes order from webhook

### Webhook Handlers
- `whatsappcrm_backend/meta_integration/views.py`:
  - `_handle_message()` - Routes incoming messages
  - `_handle_order_message()` - Handles catalog order messages

### Payment Integration
- `whatsappcrm_backend/paynow_integration/views.py`:
  - `initiate_whatsapp_payment()` - Payment initiation endpoint
  - `paynow_ipn_handler()` - Payment callback handler

### URLs
- `whatsappcrm_backend/paynow_integration/urls.py` - Payment endpoints
- `whatsappcrm_backend/flows/urls.py` - Flow management endpoints

## Models Involved

### Order Management
- `customer_data.models.Order` - Order records with payment status
- `customer_data.models.OrderItem` - Individual items in an order
- `customer_data.models.CustomerProfile` - Customer information

### Product Management
- `products_and_services.models.Product` - Product catalog with SKUs

### Payment Management
- `customer_data.models.Payment` - Payment records
- `paynow_integration.models.PaynowConfig` - Paynow configuration

### WhatsApp Integration
- `flows.models.WhatsAppFlow` - WhatsApp Flow definitions
- `meta_integration.models.MetaAppConfig` - WhatsApp Business API configuration

## Configuration Requirements

### 1. Meta App Configuration
- Must have an active MetaAppConfig with catalog_id configured
- Catalog products must be synced to Meta

### 2. WhatsApp Flow Setup
- A WhatsApp Flow named 'payment_flow' should be created and published
- The flow should have a payment screen that collects:
  - Payment method
  - Phone number
  - Email (optional)
- The flow should be configured to send data to the payment endpoint

### 3. Paynow Configuration
- PaynowConfig must be set up with:
  - Integration ID
  - Integration Key
  - IPN URL: `https://yourdomain.com/api/crm-api/paynow/ipn/`

## Testing the Flow

### 1. Test Catalog Message
Send "menu" to the WhatsApp number and select "Shop Products"

### 2. Test Order Processing
- Browse the catalog in WhatsApp
- Add items to cart
- Submit the order
- Verify:
  - Order created in database
  - Confirmation message received
  - Payment flow message sent

### 3. Test Payment
- Complete the payment form in WhatsApp Flow
- Verify:
  - Payment record created
  - Paynow transaction initiated
  - User receives payment instructions

### 4. Test Payment Completion
- Complete payment in Ecocash/OneMoney
- Verify:
  - IPN callback received
  - Payment status updated
  - Order payment status updated
  - Confirmation message sent to user

## API Endpoints

### Payment Initiation
```
POST /api/crm-api/paynow/initiate-payment/
Content-Type: application/json

{
    "order_number": "WA-12345",
    "phone_number": "263771234567",
    "email": "customer@example.com",
    "amount": "100.00",
    "payment_method": "ecocash",
    "currency": "USD"
}
```

Response:
```json
{
    "success": true,
    "message": "Payment initiated successfully",
    "payment_id": "uuid-here",
    "payment_reference": "PAY-WA-12345-ABC123",
    "poll_url": "https://paynow.co.zw/poll/...",
    "paynow_reference": "123456",
    "instructions": "Please check your ecocash to complete the payment."
}
```

### Payment IPN Callback
```
POST /api/crm-api/paynow/ipn/
Content-Type: application/x-www-form-urlencoded

reference=PAY-WA-12345-ABC123&
paynowreference=123456&
amount=100.00&
status=Paid&
pollurl=https://...&
hash=...
```

## Security Considerations

1. **Signature Verification**: Webhook messages are verified using X-Hub-Signature-256
2. **IPN Hash Verification**: Payment callbacks are verified using Paynow hash
3. **Anonymous Endpoints**: Payment endpoint allows anonymous access for WhatsApp Flow integration
4. **CSRF Exemption**: IPN handler is CSRF-exempt as required by Paynow

## Troubleshooting

### Catalog Not Showing
- Verify MetaAppConfig has catalog_id set
- Ensure products are synced to Meta catalog
- Check that products have valid SKUs

### Order Not Created
- Check webhook logs in WebhookEventLog
- Verify products exist in database with matching SKUs
- Check Order model for validation errors

### Payment Not Initiating
- Verify WhatsApp Flow is published
- Check PaynowConfig is properly configured
- Ensure payment endpoint is accessible
- Review logs for initiate_whatsapp_payment errors

### Payment Not Completing
- Verify IPN URL is accessible from Paynow servers
- Check payment hash verification
- Review paynow_ipn_handler logs

## Future Enhancements

Potential improvements:
1. Add cart persistence in flow context
2. Support for cart modifications before checkout
3. Multiple payment methods in flow
4. Order tracking via WhatsApp
5. Refund processing
6. Partial payment support

## Conclusion

The implementation is **complete** and production-ready. All three requirements have been fulfilled:

1. ✅ Shop Now option opens the WhatsApp catalog
2. ✅ Cart orders from users are processed and stored
3. ✅ Payment initiation flow with endpoint is implemented

The system provides an end-to-end shopping experience through WhatsApp, from browsing products to completing payment.
