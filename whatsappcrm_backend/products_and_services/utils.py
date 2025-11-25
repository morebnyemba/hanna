import re
from decimal import Decimal

def generate_sku(product):
    """Generate a deterministic SKU for a product if one is missing.
    Pattern: CC-BBB-SPEC-NNN
    CC: first 2 letters of category or PT fallback
    BBB: first 3 letters of brand or GEN
    SPEC: extracted capacity/watt/version token or BASE
    NNN: sequential number within (category, brand, spec) group (zero padded)
    """
    category_code = 'PT'
    if product.category and product.category.name:
        category_code = re.sub(r'[^A-Za-z]', '', product.category.name.upper())[:2] or 'PT'
    brand_code = 'GEN'
    if product.brand:
        brand_code = re.sub(r'[^A-Za-z]', '', product.brand.upper())[:3] or 'GEN'
    # Extract spec token from name/description (e.g., 5kVA, 550W, 200Ah)
    text = f"{product.name} {product.description or ''}".upper()
    spec_match = re.search(r'(\d+\s?KVA|\d+\s?KW|\d+\s?W|\d+\s?AH|\d+\s?AMP|\d+\s?A|\d+V)', text)
    spec_token = spec_match.group(0).replace(' ', '') if spec_match else 'BASE'
    from .models import Product
    base_queryset = Product.objects.filter(category=product.category, brand=product.brand)
    similar = base_queryset.filter(sku__startswith=f"{category_code}-{brand_code}-{spec_token}")
    seq = similar.count() + 1
    seq_part = f"{seq:03d}"  # zero pad to 3 digits
    sku = f"{category_code}-{brand_code}-{spec_token}-{seq_part}"
    return sku
