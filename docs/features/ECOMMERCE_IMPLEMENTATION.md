# Hanna E-Commerce Implementation Guide

## Overview

This document describes the e-commerce functionality added to the Hanna platform, including the digital shop landing page, shopping cart system, and backend API integration.

## Architecture

### Backend (Django REST Framework)

#### Models

**Cart Model** (`whatsappcrm_backend/products_and_services/models.py`)
```python
class Cart(models.Model):
    user = ForeignKey(AUTH_USER_MODEL)  # Null for guest carts
    session_key = CharField()  # For guest cart identification
    created_at = DateTimeField()
    updated_at = DateTimeField()
    
    @property
    def total_items  # Sum of all item quantities
    @property
    def total_price  # Sum of all item subtotals
```

**CartItem Model**
```python
class CartItem(models.Model):
    cart = ForeignKey(Cart)
    product = ForeignKey(Product)
    quantity = PositiveIntegerField()
    created_at = DateTimeField()
    updated_at = DateTimeField()
    
    @property
    def subtotal  # product.price * quantity
    
    class Meta:
        unique_together = ['cart', 'product']  # One entry per product per cart
```

#### API Endpoints

All endpoints are under `/crm-api/products/cart/`:

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| GET | `/cart/` | Get current user/session cart | - | Cart with items |
| POST | `/cart/add/` | Add product to cart | `{product_id, quantity}` | Updated cart |
| POST | `/cart/update/` | Update item quantity | `{cart_item_id, quantity}` | Updated cart |
| POST | `/cart/remove/` | Remove item from cart | `{cart_item_id}` | Updated cart |
| POST | `/cart/clear/` | Clear all items | - | Empty cart |

#### Features

- **Guest Cart Support**: Uses Django session keys for anonymous users
- **User Cart Persistence**: Authenticated users have persistent carts
- **Stock Validation**: Validates stock availability on add/update operations
- **Automatic Calculations**: Cart totals and item subtotals calculated dynamically
- **Django Admin Integration**: Full CRUD operations available in admin panel

### Frontend (Next.js 16 + TypeScript)

#### Landing Page Updates

**File**: `hanna-management-frontend/app/page.tsx`

Changes made:
- Updated tagline to emphasize e-commerce capabilities
- Added "Digital Shop", "Warranty Management", and "Order Tracking" feature cards
- Prominent "Visit Our Digital Shop" CTA button
- Added trust indicators (Fast Delivery, Secure Payments, 24/7 Support)
- Reorganized portal links into "Business Management Portals" section

#### Digital Shop Page

**File**: `hanna-management-frontend/app/client/shop/page.tsx`

**Key Components**:

1. **Header**
   - Home navigation link
   - Shop title
   - Cart button with item count badge

2. **Category Filter**
   - Dynamic category buttons
   - "All Products" default view
   - Filters products by selected category

3. **Product Grid**
   - Responsive grid layout (1-4 columns based on screen size)
   - Product cards with:
     - Placeholder image area
     - Product name and description
     - Price display
     - Stock indicator
     - "Add to Cart" button

4. **Shopping Cart Sidebar**
   - Slide-out panel from the right
   - Cart item list with:
     - Product image placeholder
     - Product name and unit price
     - Quantity controls (+/-)
     - Remove button
     - Item subtotal
   - Cart summary:
     - Total items count
     - Total price
     - "Proceed to Checkout" button
     - "Clear Cart" button

**State Management**:
```typescript
const [products, setProducts] = useState<Product[]>([]);
const [cart, setCart] = useState<Cart | null>(null);
const [loading, setLoading] = useState(true);
const [cartLoading, setCartLoading] = useState(false);
const [showCart, setShowCart] = useState(false);
const [selectedCategory, setSelectedCategory] = useState<string>('all');
```

**API Integration**:
```typescript
// Fetch products from backend
fetchProducts() => GET /crm-api/products/products/

// Fetch current cart
fetchCart() => GET /crm-api/products/cart/

// Add to cart
addToCart(productId, quantity) => POST /crm-api/products/cart/add/

// Update quantity
updateCartItem(cartItemId, quantity) => POST /crm-api/products/cart/update/

// Remove from cart
removeFromCart(cartItemId) => POST /crm-api/products/cart/remove/

// Clear cart
clearCart() => POST /crm-api/products/cart/clear/
```

## Setup Instructions

### Backend Setup

1. **Run Migrations**
   ```bash
   cd whatsappcrm_backend
   python manage.py makemigrations products_and_services
   python manage.py migrate
   ```

2. **Create Sample Products** (optional)
   ```bash
   python manage.py shell
   ```
   ```python
   from products_and_services.models import Product, ProductCategory
   
   # Create category
   category = ProductCategory.objects.create(
       name="Electronics",
       description="Electronic devices and accessories"
   )
   
   # Create products
   Product.objects.create(
       name="Laptop",
       description="High-performance laptop",
       price=999.99,
       currency="USD",
       stock_quantity=10,
       product_type="hardware",
       category=category,
       is_active=True
   )
   ```

3. **Start Backend Server**
   ```bash
   python manage.py runserver
   ```

### Frontend Setup

1. **Install Dependencies**
   ```bash
   cd hanna-management-frontend
   npm install
   ```

2. **Configure API URL**
   
   Create/update `.env.local`:
   ```env
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```

4. **Access the Shop**
   - Landing page: http://localhost:3000
   - Digital shop: http://localhost:3000/client/shop

## Usage Examples

### Adding Products via Django Admin

1. Navigate to: http://localhost:8000/admin/
2. Go to "Products and Services" > "Products"
3. Click "Add Product"
4. Fill in required fields:
   - Name
   - Price
   - Stock Quantity
   - Product Type
   - Is Active (checked)
5. Save

### Shopping Flow

1. **Browse Products**
   - Visit `/client/shop`
   - View all available products
   - Filter by category if desired

2. **Add to Cart**
   - Click "Add to Cart" on any product
   - Cart sidebar opens automatically
   - Item appears in cart with quantity 1

3. **Manage Cart**
   - Click "+/-" to adjust quantities
   - Click trash icon to remove items
   - Click "Clear Cart" to empty cart
   - View running total at bottom

4. **Checkout** (To be implemented)
   - Click "Proceed to Checkout"
   - Future: Payment processing, order confirmation

## API Request/Response Examples

### Get Cart
```http
GET /crm-api/products/cart/
```

Response:
```json
{
  "id": 1,
  "user": null,
  "session_key": "abc123xyz",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Laptop",
        "price": "999.99",
        "currency": "USD",
        "stock_quantity": 10,
        ...
      },
      "quantity": 2,
      "subtotal": "1999.98"
    }
  ],
  "total_items": 2,
  "total_price": "1999.98",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z"
}
```

### Add to Cart
```http
POST /crm-api/products/cart/add/
Content-Type: application/json

{
  "product_id": 1,
  "quantity": 2
}
```

Response:
```json
{
  "message": "Added 2x Laptop to cart",
  "cart": {
    "id": 1,
    "items": [...],
    "total_items": 2,
    "total_price": "1999.98"
  }
}
```

### Update Quantity
```http
POST /crm-api/products/cart/update/
Content-Type: application/json

{
  "cart_item_id": 1,
  "quantity": 3
}
```

### Remove Item
```http
POST /crm-api/products/cart/remove/
Content-Type: application/json

{
  "cart_item_id": 1
}
```

## Security Considerations

1. **Stock Validation**: Backend validates stock availability before adding/updating
2. **Session Security**: Guest carts use Django's secure session framework
3. **Input Validation**: All API inputs validated with DRF serializers
4. **Price Integrity**: Prices calculated on backend, not accepted from frontend
5. **Authentication**: Cart operations work for both authenticated and anonymous users

## Testing

### Manual Testing Checklist

- [ ] Products display correctly on shop page
- [ ] Category filtering works
- [ ] Add to cart adds items with correct quantity
- [ ] Cart badge shows correct item count
- [ ] Quantity increase/decrease works
- [ ] Remove item removes from cart
- [ ] Clear cart empties all items
- [ ] Stock validation prevents over-ordering
- [ ] Cart persists across page refreshes (for authenticated users)
- [ ] Guest cart works with session

### API Testing with curl

```bash
# Get cart
curl http://localhost:8000/crm-api/products/cart/

# Add to cart
curl -X POST http://localhost:8000/crm-api/products/cart/add/ \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity": 2}'

# Update quantity
curl -X POST http://localhost:8000/crm-api/products/cart/update/ \
  -H "Content-Type: application/json" \
  -d '{"cart_item_id": 1, "quantity": 3}'

# Remove item
curl -X POST http://localhost:8000/crm-api/products/cart/remove/ \
  -H "Content-Type: application/json" \
  -d '{"cart_item_id": 1}'

# Clear cart
curl -X POST http://localhost:8000/crm-api/products/cart/clear/
```

## Future Enhancements

### Phase 2 - Checkout & Orders
- [ ] Checkout page with shipping/billing forms
- [ ] Payment gateway integration (Stripe, PayPal, etc.)
- [ ] Order model and API endpoints
- [ ] Order confirmation emails
- [ ] Order history page

### Phase 3 - Enhanced Features
- [ ] Product search functionality
- [ ] Product detail pages
- [ ] Product reviews and ratings
- [ ] Wishlist functionality
- [ ] Product recommendations
- [ ] Discount codes/coupons
- [ ] Inventory management
- [ ] Multi-currency support

### Phase 4 - User Experience
- [ ] Product image uploads and display
- [ ] Advanced filtering (price range, ratings, etc.)
- [ ] Sorting options (price, popularity, newest)
- [ ] Quick view modal
- [ ] Recently viewed products
- [ ] Email notifications
- [ ] SMS notifications via WhatsApp integration

## Troubleshooting

### Products Not Loading
- Check backend is running: `http://localhost:8000/crm-api/products/products/`
- Verify NEXT_PUBLIC_API_BASE_URL in frontend .env.local
- Check browser console for CORS errors
- Ensure products have `is_active=True`

### Cart Not Updating
- Check backend cart endpoint: `http://localhost:8000/crm-api/products/cart/`
- Verify session cookies are being sent
- Check backend logs for errors
- Clear browser cache/cookies

### Stock Validation Issues
- Verify product `stock_quantity` is set correctly
- Check backend response for validation errors
- Update stock quantities in Django admin

## Support

For issues or questions:
1. Check this documentation
2. Review backend logs: `whatsappcrm_backend/`
3. Review frontend console: Browser Developer Tools
4. Contact development team

## License

© 2025 Pfungwa Technologies. All rights reserved.
