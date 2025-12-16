# AI Shopping Assistant - Quick Reference

## Quick Start

### Accessing the Feature
1. User sends "menu" or "hello" to WhatsApp bot
2. Select "🛍️ AI Shopping Assistant" from the menu
3. Describe your product requirements
4. Choose to buy or get a recommendation

## Developer Quick Reference

### File Structure
```
whatsappcrm_backend/
├── conversations/models.py           # Added 'ai_shopping' mode
├── flows/
│   ├── tasks.py                      # handle_ai_shopping_task()
│   ├── actions.py                    # Cart & PDF actions
│   ├── services.py                   # AI mode routing
│   └── definitions/
│       └── main_menu_flow.py         # Menu integration
└── products_and_services/models.py   # Cart & CartItem models
```

### Key Functions

#### Starting AI Shopping Session
```python
# In main_menu_flow.py
{
    "name": "start_ai_shopping_session",
    "type": "action",
    "config": {
        "actions_to_run": [{
            "action_type": "update_contact_field",
            "field_path": "conversation_mode",
            "value_template": "ai_shopping"
        }]
    }
}
```

#### AI Shopping Task
```python
# In flows/tasks.py
@shared_task(name="flows.handle_ai_shopping_task")
def handle_ai_shopping_task(contact_id: int, message_id: int):
    """
    Main AI shopping assistant task
    - Loads product catalog
    - Processes user requirements
    - Generates recommendations
    - Handles cart operations
    - Creates PDF reports
    """
```

#### Adding Products to Cart
```python
# In flows/actions.py
def add_products_to_cart_bulk(contact, context, params):
    """
    Params:
        product_ids: [1, 2, 3]  # List of product IDs
        quantities: [1, 2, 1]    # Optional quantities
    
    Returns context with:
        cart_id, cart_total_items, cart_total_price, added_products
    """
```

#### Generating PDF
```python
# In flows/actions.py
def generate_shopping_recommendation_pdf(contact, context, params):
    """
    Params:
        product_ids: [1, 2, 3]
        user_requirements: "solar system for..."
        ai_analysis: "Based on your needs..."
    
    Returns context with:
        recommendation_pdf_path, recommendation_pdf_url
    """
```

### Control Tokens

| Token | Purpose | Example |
|-------|---------|---------|
| `PRODUCT_IDS: [1,2,3]` | List recommended products | Display only |
| `ADD_TO_CART: [1,2,3]` | Add products to cart | Triggers cart action |
| `GENERATE_PDF: [1,2,3]` | Generate PDF report | Triggers PDF generation |
| `[HUMAN_HANDOVER]` | Escalate to human | Exits AI mode |
| `[END_CONVERSATION]` | End session | Returns to menu |

### AI System Prompt Structure

```
1. Core Directives
   - Customer Focus
   - Product Knowledge
   - Efficiency Protocol
   - Language Adaptability

2. Product Catalog (Live Database)
   - ID, Name, Price, Category
   - Description, Stock
   - Up to 50 products loaded

3. Standard Operating Procedure
   Step 1: Requirements Gathering
   Step 2: Analysis & Recommendation  
   Step 3: Purchase Intent
   Step 4: Action Execution

4. Example Interactions
```

### Testing Commands

```bash
# Validate syntax
cd whatsappcrm_backend
python -m py_compile flows/tasks.py flows/actions.py

# Test control token parsing
python3 << 'EOF'
import re
response = "ADD_TO_CART: [123, 456]"
match = re.search(r'ADD_TO_CART:\s*\[([\d,\s]+)\]', response)
ids = [int(i.strip()) for i in match.group(1).split(',')]
print(f"Parsed IDs: {ids}")
EOF

# Check flow structure
python3 << 'EOF'
from flows.definitions.main_menu_flow import MAIN_MENU_FLOW
steps = [s['name'] for s in MAIN_MENU_FLOW['steps']]
print(f"AI Shopping steps: {[s for s in steps if 'shopping' in s]}")
EOF
```

### Common Modifications

#### Adding New Product Fields to AI Context
```python
# In handle_ai_shopping_task()
products = Product.objects.filter(is_active=True).values(
    'id', 'name', 'description', 'price', 
    'category__name', 'product_type', 'stock_quantity',
    # Add new fields here:
    'brand', 'warranty_period', 'specifications'
)
```

#### Customizing PDF Layout
```python
# In generate_shopping_recommendation_pdf()
# Modify the story list to add/remove sections
story.append(Paragraph("New Section", heading_style))
story.append(Table(data, colWidths=[...]))
```

#### Adjusting AI Behavior
```python
# In handle_ai_shopping_task()
# Modify the system_prompt variable to change:
# - Tone and personality
# - Response format
# - Recommendation logic
# - Language instructions
```

### Database Queries

```python
# Get active products for catalog
products = Product.objects.filter(
    is_active=True,
    stock_quantity__gt=0
).select_related('category')

# Get user's cart
cart = Cart.objects.filter(
    session_key=contact.whatsapp_id
).prefetch_related('items__product').first()

# Get cart total
total = sum(item.subtotal for item in cart.items.all())
```

### Logging

```python
# Task logs
logger.info(f"[AI Shopping Task for Contact: {contact_id}] Message")

# Action logs  
logger.info(f"Added {quantity}x {product.name} to cart for contact {contact.id}")

# Error logs
logger.error(f"Error in AI shopping task: {e}", exc_info=True)
```

### Configuration Checklist

- [ ] AIProvider with provider='google_gemini' is active
- [ ] Google Gemini API key is configured
- [ ] Products exist with is_active=True
- [ ] MEDIA_ROOT/recommendations/ directory exists
- [ ] Celery workers are running
- [ ] MetaAppConfig is active

### Troubleshooting Quick Fixes

| Issue | Solution |
|-------|----------|
| AI not responding | Check Celery workers, AI provider API key |
| Products not found | Set `is_active=True` on products |
| PDF not generated | Check MEDIA_ROOT permissions, install reportlab |
| Cart not working | Verify Cart/CartItem models migrated |
| Wrong language | AI auto-detects, check user's message language |

### Exit Keywords

Users can exit AI mode by sending:
- `exit`
- `menu`
- `stop`
- `quit`

These return user to main menu flow.

## API Integration Points

### Message Flow
```
WhatsApp → Meta Webhook → Django View → Celery Task → AI Handler
                                                      ↓
                                              Gemini API
                                                      ↓
                                         Response Processing
                                                      ↓
                            Cart Actions / PDF Generation / Reply
```

### Task Chain
```
handle_ai_shopping_task()
├── Load product catalog
├── Build AI context with history
├── Send to Gemini API
├── Parse response for control tokens
├── Execute actions (cart/PDF)
└── Send reply via send_whatsapp_message_task
```

## Performance Considerations

- Product catalog limited to 50 items (token limit)
- PDF generation is synchronous (consider async for large catalogs)
- Cart operations are fast (simple DB inserts)
- AI response time: 2-5 seconds typically

## Security Notes

- WhatsApp ID used as cart session_key (secure, unique)
- PDF files saved to MEDIA_ROOT (not publicly accessible)
- No sensitive data in AI prompts
- Product IDs validated before cart addition

## Support Resources

- Full Documentation: `AI_SHOPPING_ASSISTANT_GUIDE.md`
- Main Menu Flow: `flows/definitions/main_menu_flow.py`
- AI Task: `flows/tasks.py:handle_ai_shopping_task()`
- Actions: `flows/actions.py`
- Models: `conversations/models.py`, `products_and_services/models.py`
