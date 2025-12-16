# AI Shopping Assistant Implementation Guide

## Overview

The AI Shopping Assistant is an intelligent conversational interface that helps customers find and purchase solar products based on their specific requirements. It leverages Google Gemini AI to understand customer needs, recommend appropriate products, and facilitate purchases through an intuitive WhatsApp-based conversation.

## Features

### 1. **Intelligent Product Recommendations**
- Analyzes customer requirements (e.g., "solar system for 2 fridges, 4 TVs, 2 lights")
- Searches the product database for matching items
- Provides detailed product specifications and pricing
- Calculates total system cost

### 2. **Seamless Cart Integration**
- Automatically adds recommended products to cart
- Shows real-time cart totals
- Supports bulk product additions

### 3. **PDF Recommendation Reports**
- Generates branded PDF documents with:
  - Customer information
  - Requirements analysis
  - AI recommendations
  - Product details and specifications
  - Total pricing
  - Next steps and contact information
- Professional Pfungwa branding

### 4. **Multi-Language Support**
- Automatically detects and responds in the user's language
- Maintains language consistency throughout the conversation

### 5. **Human Handover**
- Seamlessly escalates complex queries to human agents
- Maintains conversation context

## Architecture

### Components

#### 1. **Conversation Mode** (`conversations/models.py`)
```python
CONVERSATION_MODE_CHOICES = [
    ('flow', 'Flow-based Conversation'),
    ('ai_troubleshooting', 'AI Troubleshooting Mode'),
    ('ai_shopping', 'AI Shopping Assistant Mode'),
]
```

#### 2. **AI Shopping Task** (`flows/tasks.py`)
- **Function**: `handle_ai_shopping_task(contact_id, message_id)`
- **Purpose**: Manages the AI conversation for shopping assistance
- **Key Features**:
  - Loads product catalog into AI context
  - Parses control tokens (PRODUCT_IDS, ADD_TO_CART, GENERATE_PDF)
  - Handles cart operations
  - Generates PDF recommendations
  - Manages conversation state

#### 3. **Flow Actions** (`flows/actions.py`)

##### `add_products_to_cart_bulk`
- Adds multiple products to cart at once
- Creates or updates cart items
- Tracks cart totals
- Saves cart information to context

##### `generate_shopping_recommendation_pdf`
- Creates branded PDF documents
- Uses ReportLab for PDF generation
- Includes customer info, requirements, and recommendations
- Saves PDF to media directory

#### 4. **Main Menu Integration** (`flows/definitions/main_menu_flow.py`)
- Adds "🛍️ AI Shopping Assistant" option
- Creates flow steps for session initialization
- Provides welcome message with instructions

#### 5. **Service Router** (`flows/services.py`)
- Routes `ai_shopping` conversation mode to appropriate handler
- Manages conversation mode transitions

## Usage Flow

### 1. **Starting a Session**

User selects "🛍️ AI Shopping Assistant" from main menu:

```
🛍️ Welcome to your AI Shopping Assistant!

I'm Hanna, and I'm here to help you find the perfect solar products for your needs.

*How it works:*
1. Tell me what you need (e.g., 'I need a solar system for 2 fridges, 4 TVs, and 2 lights')
2. I'll analyze your requirements and recommend products
3. You can either buy immediately or get a detailed PDF recommendation

*What can I help you with today?*

Type 'menu' at any time to return to the main menu.
```

### 2. **Customer Describes Requirements**

```
User: "I need a solar system that can power 2 fridges, 4 TVs, and 2 lights"
```

### 3. **AI Analyzes and Recommends**

```
Hanna: "I'll help you find the perfect solar system! Based on your requirements 
(2 fridges, 4 TVs, 2 lights), I estimate you'll need approximately 3-4kW system.

Here are my recommendations:

**1. Solar Flex Pro 5kW Inverter** - $2,500 USD
   - Perfect for your load requirements
   - Pure sine wave output
   - Built-in MPPT controller

**2. 8x 550W Solar Panels** - $1,600 USD
   - High efficiency panels
   - 25-year warranty

**3. 10kWh Lithium Battery Bank** - $3,200 USD
   - Provides backup power
   - Long lifespan

**Estimated Total: $7,300 USD**

PRODUCT_IDS: [123, 456, 789]

Would you like to:
1. 💳 **BUY NOW** - Add these products to your cart
2. 📄 **GET RECOMMENDATION** - Receive a detailed PDF analysis"
```

### 4. **Purchase or Get Recommendation**

#### Option A: Buy Now
```
User: "BUY NOW"

Hanna: "Great choice! Let me add these to your cart...
ADD_TO_CART: [123, 456, 789]

✅ **Products Added to Cart!**

**Total Items:** 3
**Total Price:** $7,300 USD

To complete your order, reply with **CHECKOUT** or type **VIEW CART** to review."
```

#### Option B: Get Recommendation
```
User: "GET RECOMMENDATION"

Hanna: "I'll prepare a detailed analysis for you...
GENERATE_PDF: [123, 456, 789]

📄 **Recommendation Report Generated!**

I've prepared a detailed analysis for you. The document will be sent shortly."

[PDF document is sent via WhatsApp]
```

## Control Tokens

The AI uses special control tokens to trigger backend actions:

### `PRODUCT_IDS: [id1, id2, id3]`
- Lists recommended product IDs
- Used for tracking and reference

### `ADD_TO_CART: [id1, id2, id3]`
- Triggers bulk cart addition
- Adds specified products to user's cart
- Shows cart summary

### `GENERATE_PDF: [id1, id2, id3]`
- Generates branded PDF recommendation
- Includes specified products
- Sends as WhatsApp document

### `[HUMAN_HANDOVER]`
- Escalates to human agent
- Sets needs_human_intervention flag
- Exits AI mode

### `[END_CONVERSATION]`
- Ends shopping session
- Returns to flow mode
- Clears conversation state

## AI System Prompt

The AI is configured with a comprehensive system prompt that includes:

1. **Core Directives**:
   - Customer focus
   - Product knowledge
   - Efficiency protocol
   - Language adaptability
   - Database integration

2. **Product Catalog**:
   - Live product database integration
   - Up to 50 most relevant products
   - Includes: ID, name, price, category, type, stock

3. **Standard Operating Procedure**:
   - Requirements gathering
   - Analysis & recommendation
   - Purchase intent clarification
   - Action execution

4. **Example Interactions**:
   - Demonstrates proper formatting
   - Shows control token usage
   - Illustrates conversation flow

## PDF Report Structure

The generated PDF includes:

1. **Header**
   - Pfungwa Solar Solutions branding
   - Document title: "AI-Powered Product Recommendation"

2. **Customer Information**
   - Contact name/WhatsApp ID
   - Date and time

3. **Requirements Section**
   - User's stated requirements

4. **AI Analysis**
   - Detailed analysis and recommendations
   - System sizing calculations

5. **Product Table**
   - Product names
   - Descriptions
   - Prices
   - Total cost

6. **Next Steps**
   - Instructions for ordering
   - Contact information

7. **Footer**
   - Company details
   - WhatsApp and email
   - "Powered by AI-driven recommendations" tagline

## Database Schema

### Cart Model
```python
class Cart(models.Model):
    user = ForeignKey(User, null=True, blank=True)
    session_key = CharField(max_length=255)  # WhatsApp ID for guests
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

### CartItem Model
```python
class CartItem(models.Model):
    cart = ForeignKey(Cart, related_name='items')
    product = ForeignKey(Product)
    quantity = PositiveIntegerField(default=1)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

## Configuration

### Required Settings

1. **AI Provider**:
   - Active Google Gemini AI provider configured
   - API key in `ai_integration.AIProvider`

2. **Media Directory**:
   - `MEDIA_ROOT/recommendations/` directory for PDFs
   - Write permissions for application

3. **Product Catalog**:
   - Active products with proper details:
     - Name, description, price, currency
     - Category, product type
     - Stock quantity

### Environment Variables
```bash
# Already configured in existing .env
GOOGLE_GEMINI_API_KEY=your_api_key_here
```

## Testing

### Manual Testing Checklist

1. **Basic Flow**:
   - [ ] Select AI Shopping Assistant from menu
   - [ ] Receive welcome message
   - [ ] Describe requirements
   - [ ] Receive product recommendations

2. **Cart Operations**:
   - [ ] Request to buy products
   - [ ] Products added to cart
   - [ ] Cart totals displayed correctly
   - [ ] Multiple products handled

3. **PDF Generation**:
   - [ ] Request recommendation
   - [ ] PDF generated successfully
   - [ ] PDF sent via WhatsApp
   - [ ] Branding correct
   - [ ] All information included

4. **Edge Cases**:
   - [ ] Exit with 'menu' keyword
   - [ ] Human handover for complex queries
   - [ ] No products match requirements
   - [ ] Invalid product IDs

### Automated Tests

```python
# Test control token parsing
def test_control_token_parsing():
    response = "PRODUCT_IDS: [123, 456]"
    match = re.search(r'PRODUCT_IDS:\s*\[([\d,\s]+)\]', response)
    assert match is not None
    product_ids = [int(pid.strip()) for pid in match.group(1).split(',')]
    assert product_ids == [123, 456]

# Test cart addition
def test_add_to_cart():
    context = {}
    params = {'product_ids': [1, 2, 3], 'quantities': [1, 2, 1]}
    add_products_to_cart_bulk(contact, context, params)
    assert 'cart_id' in context
    assert context['cart_total_items'] == 4
```

## Troubleshooting

### Common Issues

1. **AI Not Responding**:
   - Check AIProvider is active and has valid API key
   - Check Celery workers are running
   - Review logs for Gemini API errors

2. **Products Not Found**:
   - Verify products are marked as `is_active=True`
   - Check product catalog is loading in AI prompt
   - Ensure product IDs are integers

3. **PDF Not Generated**:
   - Check `MEDIA_ROOT/recommendations/` directory exists
   - Verify write permissions
   - Check ReportLab is installed
   - Review PDF generation logs

4. **Cart Not Working**:
   - Verify Cart and CartItem models exist
   - Check database migrations are applied
   - Ensure session_key is set correctly

## Future Enhancements

1. **Enhanced Product Search**:
   - Vector embeddings for semantic search
   - Better product matching algorithms
   - Category-based filtering

2. **Cart Features**:
   - Cart modification (remove/update quantities)
   - Save cart for later
   - Cart expiration handling

3. **PDF Improvements**:
   - Product images in PDF
   - Installation diagrams
   - Energy calculations
   - ROI analysis

4. **Analytics**:
   - Track popular product combinations
   - Conversion rate from recommendations
   - Common customer requirements
   - AI performance metrics

5. **Multi-turn Conversations**:
   - Remember previous conversations
   - Follow-up questions
   - Comparison requests
   - Bundle deals

## Support

For issues or questions:
- **Technical Support**: Review logs in `flows/tasks.py`
- **AI Behavior**: Check system prompt in `handle_ai_shopping_task`
- **Cart Issues**: Check `flows/actions.py` cart functions
- **PDF Problems**: Check ReportLab in `generate_shopping_recommendation_pdf`

## Credits

**Implementation**: Copilot AI Agent  
**Client**: Pfungwa Solar Solutions  
**AI Engine**: Google Gemini 2.5 Flash  
**Framework**: Django + Celery  
**PDF Generation**: ReportLab
