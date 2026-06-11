from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid

class ProductCategory(models.Model):
    """
    A category for organizing products.
    """
    name = models.CharField(_("Category Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='children',
        help_text=_("Parent category for creating a hierarchy (e.g., 'Software' -> 'Accounting').")
    )
    google_product_category = models.CharField(
        _("Google Product Category"), 
        max_length=255, 
        blank=True, 
        null=True, 
        help_text=_("Google Product Category for Meta Catalog (e.g., 'Apparel & Accessories > Clothing' or category ID like '212'). All products in this category will use this mapping.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = _("Product Category")
        verbose_name_plural = _("Product Categories")
        ordering = ['name']


class Product(models.Model):
    """
    A generic model for all sellable items, including software, hardware, and services.
    """
    class ProductType(models.TextChoices):
        SOFTWARE = 'software', _('Software Package')
        SERVICE = 'service', _('Professional Service')
        HARDWARE = 'hardware', _('Hardware Device')
        MODULE = 'module', _('Software Module')

    class LicenseType(models.TextChoices):
        SUBSCRIPTION = 'subscription', _('Subscription')
        PERPETUAL = 'perpetual', _('Perpetual License')
        ONE_TIME = 'one_time', _('One-Time Purchase')

    name = models.CharField(_("Product Name"), max_length=255)
    sku = models.CharField(_("SKU / Product Code"), max_length=100, unique=True, blank=True, null=True)
    barcode = models.CharField(_("Barcode"), max_length=100, unique=True, blank=True, null=True, db_index=True, help_text=_("Barcode value for product identification"))
    description = models.TextField(_("Description"), blank=True, null=True)
    product_type = models.CharField(_("Product Type"), max_length=20, choices=ProductType.choices, db_index=True)
    category = models.ForeignKey(
        ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    is_active = models.BooleanField(_("Is Active"), default=True, help_text=_("Whether this item is available for sale."))
    website_url = models.URLField(_("Website URL"), blank=True, null=True)
    whatsapp_catalog_id = models.CharField(_("WhatsApp Catalog ID"), max_length=255, blank=True, null=True)
    country_of_origin = models.CharField(_("Country of Origin"), max_length=2, blank=True, null=True, help_text=_("The two-letter country code (e.g., US, GB) required by WhatsApp."))
    brand = models.CharField(_("Brand"), max_length=255, blank=True, null=True, help_text=_("The brand name of the product, required for WhatsApp Catalog."))
    supplier_sku = models.CharField(_("Supplier SKU"), max_length=120, blank=True, null=True, help_text=_("Original supplier or partner provided product code."))
    provisional = models.BooleanField(_("Provisional"), default=False, help_text=_("Marks products auto-created from imports pending review."))
    
    # Zoho Integration
    zoho_item_id = models.CharField(_("Zoho Item ID"), max_length=100, blank=True, null=True, unique=True, db_index=True, help_text=_("Zoho Inventory Item ID for sync tracking"))
    
    # Meta sync tracking fields
    meta_sync_attempts = models.PositiveIntegerField(_("Meta Sync Attempts"), default=0, help_text=_("Number of times sync to Meta Catalog has been attempted"))
    meta_sync_last_error = models.TextField(_("Last Meta Sync Error"), blank=True, null=True, help_text=_("Last error message from Meta API sync attempt"))
    meta_sync_last_attempt = models.DateTimeField(_("Last Meta Sync Attempt"), blank=True, null=True, help_text=_("Timestamp of last sync attempt"))
    meta_sync_last_success = models.DateTimeField(_("Last Meta Sync Success"), blank=True, null=True, help_text=_("Timestamp of last successful sync"))
    
    # --- Inventory ---
    stock_quantity = models.PositiveIntegerField(_("Stock Quantity"), default=0, help_text=_("The number of items available in stock. Used for WhatsApp Catalog inventory management."))
    featured = models.BooleanField(_("Featured"), default=False, help_text=_("Pin this product to the shop's featured section."))
    short_description = models.CharField(_("Short Description"), max_length=255, blank=True, null=True, help_text=_("Brief preview text shown on product cards. Falls back to description if empty."))
    compare_at_price = models.DecimalField(
        _("Compare-at Price"), max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Original / crossed-out price shown to indicate a discount.")
    )
    tags = models.ManyToManyField(
        'ProductTag', blank=True, related_name='products',
        help_text=_("Labels like 'New Arrival', 'Best Seller', 'On Sale'.")
    )
    weight_kg = models.DecimalField(
        _("Weight (kg)"), max_digits=8, decimal_places=3, null=True, blank=True,
        help_text=_("Used for shipping rate calculations.")
    )
    dimensions = models.JSONField(
        _("Dimensions (cm)"), default=dict, blank=True,
        help_text=_('Packed dimensions e.g. {"length": 30, "width": 20, "height": 10}')
    )

    # Software-specific fields
    license_type = models.CharField(_("License Type"), max_length=20, choices=LicenseType.choices, default=LicenseType.SUBSCRIPTION)
    dedicated_flow_name = models.CharField(
        _("Dedicated Flow Name"), max_length=255, blank=True, null=True,
        help_text=_("The name of the flow to trigger for specific follow-up on this product.")
    )
    
    # Relationships
    parent_product = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='modules', help_text=_("If this is a module, this links to the main software product."))
    compatible_products = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='compatible_with', help_text=_("e.g., A hardware device can be compatible with certain software modules."))
    manufacturer = models.ForeignKey('warranty.Manufacturer', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"
    
    def reset_meta_sync_attempts(self):
        """
        Reset Meta sync attempt counter and error.
        Useful for manual retry after fixing issues.
        """
        self.meta_sync_attempts = 0
        self.meta_sync_last_error = None
        self.save(update_fields=['meta_sync_attempts', 'meta_sync_last_error'])

    def save(self, *args, **kwargs):
        if not self.sku:
            from .utils import generate_sku
            self.sku = generate_sku(self)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['name']


class ProductTag(models.Model):
    """Flexible tags for products — New Arrival, Best Seller, On Sale, etc."""
    name = models.CharField(_("Tag Name"), max_length=50, unique=True)
    slug = models.SlugField(_("Slug"), max_length=60, unique=True)
    color = models.CharField(
        _("Badge Color"), max_length=30, default='sky',
        help_text=_("Tailwind colour name shown on the storefront badge (e.g. orange, green, sky).")
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name = _("Product Tag")
        verbose_name_plural = _("Product Tags")


class ProductVariant(models.Model):
    """
    A specific variant of a product (size, colour, kit configuration, etc.).
    e.g. "5kW Solar Kit – Blue", "Bedroom Set – Queen", "Router – Black".
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(_("Variant Name"), max_length=100, help_text=_("e.g. 'Blue / Large', '5kW Kit'"))
    sku_suffix = models.CharField(
        _("SKU Suffix"), max_length=30, blank=True, null=True,
        help_text=_("Appended to the parent SKU to form the variant SKU.")
    )
    price_override = models.DecimalField(
        _("Price Override"), max_digits=12, decimal_places=2, null=True, blank=True,
        help_text=_("Leave blank to inherit the parent product price.")
    )
    stock_quantity = models.PositiveIntegerField(_("Stock Quantity"), default=0)
    is_active = models.BooleanField(_("Is Active"), default=True)
    attributes = models.JSONField(
        _("Attributes"), default=dict, blank=True,
        help_text=_('JSON of variant attributes, e.g. {"colour": "blue", "size": "large"}')
    )
    image = models.ImageField(_("Variant Image"), upload_to='product_variant_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def effective_price(self):
        return self.price_override if self.price_override is not None else self.product.price

    def __str__(self):
        return f"{self.product.name} — {self.name}"

    class Meta:
        ordering = ['product', 'name']
        verbose_name = _("Product Variant")
        verbose_name_plural = _("Product Variants")
        unique_together = ['product', 'name']


class Coupon(models.Model):
    """Promo / discount codes redeemable at checkout."""

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Percentage Off')
        FIXED = 'fixed', _('Fixed Amount Off')
        FREE_SHIPPING = 'free_shipping', _('Free Shipping')

    code = models.CharField(_("Coupon Code"), max_length=50, unique=True, db_index=True)
    description = models.CharField(_("Description"), max_length=255, blank=True)
    discount_type = models.CharField(
        _("Discount Type"), max_length=20, choices=DiscountType.choices, default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(
        _("Discount Value"), max_digits=10, decimal_places=2, default=0,
        help_text=_("Percentage (0-100) or fixed amount depending on discount_type.")
    )
    minimum_order_amount = models.DecimalField(
        _("Minimum Order Amount"), max_digits=12, decimal_places=2, default=0,
        help_text=_("Cart total must be at least this amount before the coupon applies.")
    )
    max_uses = models.PositiveIntegerField(
        _("Max Uses"), null=True, blank=True,
        help_text=_("Leave blank for unlimited uses.")
    )
    uses = models.PositiveIntegerField(_("Times Used"), default=0, editable=False)
    max_uses_per_customer = models.PositiveIntegerField(
        _("Max Uses Per Customer"), default=1,
        help_text=_("How many times a single customer can use this coupon.")
    )
    is_active = models.BooleanField(_("Is Active"), default=True)
    valid_from = models.DateTimeField(_("Valid From"), null=True, blank=True)
    valid_until = models.DateTimeField(_("Valid Until"), null=True, blank=True)
    applicable_products = models.ManyToManyField(
        Product, blank=True, related_name='coupons',
        help_text=_("Limit coupon to specific products. Leave blank to apply to all products.")
    )
    applicable_categories = models.ManyToManyField(
        ProductCategory, blank=True, related_name='coupons',
        help_text=_("Limit coupon to specific categories. Leave blank to apply to all categories.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False, "Coupon is not active."
        if self.valid_from and now < self.valid_from:
            return False, "Coupon is not yet valid."
        if self.valid_until and now > self.valid_until:
            return False, "Coupon has expired."
        if self.max_uses is not None and self.uses >= self.max_uses:
            return False, "Coupon usage limit has been reached."
        return True, "Valid"

    def calculate_discount(self, cart_total):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            return min(cart_total, cart_total * self.discount_value / 100)
        if self.discount_type == self.DiscountType.FIXED:
            return min(cart_total, self.discount_value)
        return 0  # free_shipping handled separately

    def __str__(self):
        return f"{self.code} ({self.get_discount_type_display()})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Coupon")
        verbose_name_plural = _("Coupons")


class Wishlist(models.Model):
    """Server-side wishlist — one per session/customer."""
    session_key = models.CharField(
        _("Session Key"), max_length=255, blank=True, null=True, db_index=True
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        null=True, blank=True, related_name='wishlist'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist ({self.user or self.session_key})"

    class Meta:
        verbose_name = _("Wishlist")
        verbose_name_plural = _("Wishlists")


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='wishlist_items')
    variant = models.ForeignKey(
        ProductVariant, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='wishlist_items'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['wishlist', 'product', 'variant']
        ordering = ['-added_at']
        verbose_name = _("Wishlist Item")
        verbose_name_plural = _("Wishlist Items")

    def __str__(self):
        return f"{self.product.name} in {self.wishlist}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    reviewer_name = models.CharField(max_length=100)
    reviewer_email = models.EmailField(blank=True, null=True)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    verified_purchase = models.BooleanField(
        _("Verified Purchase"), default=False,
        help_text=_("Set automatically when the reviewer's email matches an order for this product.")
    )
    helpful_votes = models.PositiveIntegerField(_("Helpful Votes"), default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review by {self.reviewer_name} for {self.product.name} ({self.rating}/5)"


class StockNotification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_notifications')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)

    def __str__(self):
        return f"StockNotification for {self.product.name} ({self.email or self.phone})"


class ProductImage(models.Model):
    """
    An image associated with a product. Products can have multiple images.
    """
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(_("Image"), upload_to='product_images/')
    alt_text = models.CharField(
        _("Alt Text"),
        max_length=255,
        blank=True, null=True,
        help_text=_("A brief description of the image for accessibility.")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.name}"

    class Meta:
        verbose_name = _("Product Image")
        verbose_name_plural = _("Product Images")
        ordering = ['created_at']


class SerializedItem(models.Model):
    """
    Represents a single, physical instance of a product, tracked by its serial number.
    """
    class Status(models.TextChoices):
        # Stock statuses
        IN_STOCK = 'in_stock', _('In Stock')
        RESERVED = 'reserved', _('Reserved')
        
        # Sales statuses
        SOLD = 'sold', _('Sold')
        AWAITING_DELIVERY = 'awaiting_delivery', _('Awaiting Delivery')
        DELIVERED = 'delivered', _('Delivered')
        
        # Service statuses
        AWAITING_COLLECTION = 'awaiting_collection', _('Awaiting Collection')
        IN_TRANSIT = 'in_transit', _('In Transit')
        IN_REPAIR = 'in_repair', _('In Repair')
        AWAITING_PARTS = 'awaiting_parts', _('Awaiting Parts')
        OUTSOURCED = 'outsourced', _('Outsourced to Third Party')
        REPAIR_COMPLETED = 'repair_completed', _('Repair Completed')
        
        # Return/warranty statuses
        RETURNED = 'returned', _('Returned')
        WARRANTY_CLAIM = 'warranty_claim', _('Warranty Claim Processing')
        REPLACEMENT_PENDING = 'replacement_pending', _('Replacement Pending')
        
        # End-of-life statuses
        DECOMMISSIONED = 'decommissioned', _('Decommissioned')
        DISPOSED = 'disposed', _('Disposed')
    
    class Location(models.TextChoices):
        WAREHOUSE = 'warehouse', _('Warehouse')
        CUSTOMER = 'customer', _('With Customer')
        MANUFACTURER = 'manufacturer', _('At Manufacturer')
        TECHNICIAN = 'technician', _('With Technician')
        IN_TRANSIT = 'in_transit', _('In Transit')
        OUTSOURCED = 'outsourced', _('Outsourced Service')
        RETAIL = 'retail', _('Retail Store')
        DISPOSED = 'disposed', _('Disposed/Scrapped')

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='serialized_items',
        help_text=_("The generic product that this item is an instance of.")
    )
    order_item = models.ForeignKey(
        'customer_data.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_items',
        help_text=_("The order line item this physical unit is assigned to fulfill.")
    )
    serial_number = models.CharField(
        _("Serial Number"),
        max_length=255,
        unique=True,
        db_index=True,
        help_text=_("The unique serial number for this specific item.")
    )
    barcode = models.CharField(
        _("Barcode"),
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Barcode value for item identification")
    )
    status = models.CharField(
        _("Status"),
        max_length=30,
        choices=Status.choices,
        default=Status.IN_STOCK,
        db_index=True,
        help_text=_("The current status of this individual item.")
    )
    
    # Location tracking fields
    current_location = models.CharField(
        _("Current Location"),
        max_length=20,
        choices=Location.choices,
        default=Location.WAREHOUSE,
        db_index=True,
        help_text=_("The current physical location of this item.")
    )
    current_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='held_items',
        help_text=_("Current person/entity holding the item (technician, customer, etc.)")
    )
    location_notes = models.TextField(
        _("Location Notes"),
        blank=True,
        help_text=_("Additional location details or address information")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} (SN: {self.serial_number})"

    class Meta:
        verbose_name = _("Serialized Item")
        verbose_name_plural = _("Serialized Items")
        ordering = ['-created_at']


class ItemLocationHistory(models.Model):
    """
    Tracks the complete movement history of serialized items.
    Records every location change with full audit trail.
    """
    class LocationType(models.TextChoices):
        WAREHOUSE = 'warehouse', _('Warehouse')
        CUSTOMER = 'customer', _('Customer Location')
        MANUFACTURER = 'manufacturer', _('Manufacturer Facility')
        TECHNICIAN = 'technician', _('Technician/Service Center')
        IN_TRANSIT = 'in_transit', _('In Transit')
        OUTSOURCED = 'outsourced', _('Outsourced Service Provider')
        RETAIL = 'retail', _('Retail Store')
        DISPOSED = 'disposed', _('Disposed/Scrapped')
        
    class TransferReason(models.TextChoices):
        SALE = 'sale', _('Sale to Customer')
        REPAIR = 'repair', _('Repair/Service')
        WARRANTY_CLAIM = 'warranty_claim', _('Warranty Claim')
        RETURN = 'return', _('Customer Return')
        TRANSFER = 'transfer', _('Internal Transfer')
        COLLECTION = 'collection', _('Collection from Customer')
        DELIVERY = 'delivery', _('Delivery to Customer')
        OUTSOURCE = 'outsource', _('Sent for Outsourcing')
        INSTALLATION = 'installation', _('Installation at Customer Site')
        STOCK_RECEIPT = 'stock_receipt', _('Stock Receipt')
        DISPOSAL = 'disposal', _('Item Disposal')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    serialized_item = models.ForeignKey(
        SerializedItem,
        on_delete=models.CASCADE,
        related_name='location_history',
        help_text=_("The item whose location is being tracked")
    )
    from_location = models.CharField(
        _("From Location"),
        max_length=20,
        choices=LocationType.choices,
        null=True,
        blank=True,
        help_text=_("Previous location (null for initial entry)")
    )
    to_location = models.CharField(
        _("To Location"),
        max_length=20,
        choices=LocationType.choices,
        help_text=_("New location")
    )
    from_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferred_from_items',
        help_text=_("Previous holder of the item")
    )
    to_holder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transferred_to_items',
        help_text=_("New holder of the item")
    )
    transfer_reason = models.CharField(
        _("Transfer Reason"),
        max_length=20,
        choices=TransferReason.choices,
        help_text=_("Reason for the location change")
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes about this transfer")
    )
    
    # Link to related records
    related_order = models.ForeignKey(
        'customer_data.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_location_changes',
        help_text=_("Related sales order, if applicable")
    )
    related_warranty_claim = models.ForeignKey(
        'warranty.WarrantyClaim',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_location_changes',
        help_text=_("Related warranty claim, if applicable")
    )
    related_job_card = models.ForeignKey(
        'customer_data.JobCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='item_location_changes',
        help_text=_("Related job card, if applicable")
    )
    
    transferred_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='item_transfers_made',
        help_text=_("User who initiated this transfer")
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    def __str__(self):
        return f"{self.serialized_item.serial_number}: {self.from_location or 'Initial'} → {self.to_location}"
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = _("Item Location History")
        verbose_name_plural = _("Item Location Histories")
        indexes = [
            models.Index(fields=['-timestamp', 'serialized_item']),
            models.Index(fields=['to_location', '-timestamp']),
        ]


class Cart(models.Model):
    """
    Shopping cart for a user or guest session.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='carts',
        null=True,
        blank=True,
        help_text=_("The user who owns this cart. Null for guest carts.")
    )
    session_key = models.CharField(
        _("Session Key"),
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("Session identifier for guest carts")
    )
    coupon = models.ForeignKey(
        'Coupon', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='carts', help_text=_("Applied coupon code, if any.")
    )
    discount_amount = models.DecimalField(
        _("Discount Amount"), max_digits=12, decimal_places=2, default=0,
        help_text=_("Calculated discount applied to this cart.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        if self.user:
            return f"Cart for {self.user.username}"
        return f"Guest cart {self.session_key}"

    @property
    def total_items(self):
        """Total number of items in the cart"""
        return sum(item.quantity for item in self.items.all())

    @property
    def total_price(self):
        """Total price after any applied coupon discount."""
        subtotal = sum(item.subtotal for item in self.items.all())
        return max(0, subtotal - self.discount_amount)

    class Meta:
        verbose_name = _("Cart")
        verbose_name_plural = _("Carts")
        ordering = ['-updated_at']


class CartItem(models.Model):
    """
    Individual item in a shopping cart.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        help_text=_("The cart this item belongs to")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items',
        help_text=_("The product in this cart item")
    )
    quantity = models.PositiveIntegerField(
        _("Quantity"),
        default=1,
        help_text=_("Number of items")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.cart}"

    @property
    def subtotal(self):
        """Calculate subtotal for this cart item"""
        if self.product.price:
            return self.product.price * self.quantity
        return 0

    class Meta:
        verbose_name = _("Cart Item")
        verbose_name_plural = _("Cart Items")
        ordering = ['-created_at']
        unique_together = ['cart', 'product']


class SolarPackage(models.Model):
    """
    Pre-configured solar system packages for retailers to sell.
    Packages include a combination of products (inverter, panels, batteries, etc.)
    with defined system size and pricing.
    """
    name = models.CharField(
        _("Package Name"),
        max_length=255,
        help_text=_("Name of the solar package (e.g., '3kW Starter System')")
    )
    system_size = models.DecimalField(
        _("System Size (kW)"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Size of the solar system in kilowatts")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Detailed description of the package and what's included")
    )
    included_products = models.ManyToManyField(
        Product,
        through='SolarPackageProduct',
        related_name='solar_packages',
        help_text=_("Products included in this package")
    )
    price = models.DecimalField(
        _("Package Price"),
        max_digits=12,
        decimal_places=2,
        help_text=_("Total price for the complete package")
    )
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        default='USD'
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this package is available for sale")
    )
    compatibility_rules = models.JSONField(
        _("Compatibility Rules"),
        default=dict,
        blank=True,
        help_text=_("JSON field for storing compatibility validation rules")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.system_size}kW)"
    
    class Meta:
        verbose_name = _("Solar Package")
        verbose_name_plural = _("Solar Packages")
        ordering = ['system_size', 'name']


class SolarPackageProduct(models.Model):
    """
    Through model for the many-to-many relationship between SolarPackage and Product.
    Allows specifying quantity of each product in the package.
    """
    solar_package = models.ForeignKey(
        SolarPackage,
        on_delete=models.CASCADE,
        related_name='package_products'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='package_memberships'
    )
    quantity = models.PositiveIntegerField(
        _("Quantity"),
        default=1,
        help_text=_("Number of this product included in the package")
    )
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.solar_package.name}"
    
    class Meta:
        verbose_name = _("Solar Package Product")
        verbose_name_plural = _("Solar Package Products")
        unique_together = ['solar_package', 'product']


class CompatibilityRule(models.Model):
    """
    Defines compatibility rules between products.
    Used to validate system configurations (e.g., battery ↔ inverter compatibility).
    """
    class RuleType(models.TextChoices):
        REQUIRES = 'requires', _('Requires')
        COMPATIBLE = 'compatible', _('Compatible With')
        INCOMPATIBLE = 'incompatible', _('Incompatible With')
    
    name = models.CharField(
        _("Rule Name"),
        max_length=255,
        help_text=_("Descriptive name for this compatibility rule")
    )
    product_a = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='compatibility_rules_as_a',
        help_text=_("The primary product in this compatibility relationship")
    )
    product_b = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='compatibility_rules_as_b',
        help_text=_("The secondary product in this compatibility relationship")
    )
    rule_type = models.CharField(
        _("Rule Type"),
        max_length=20,
        choices=RuleType.choices,
        default=RuleType.COMPATIBLE,
        help_text=_("Type of compatibility relationship")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Additional details about this compatibility rule")
    )
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this rule is currently active and should be enforced")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}: {self.product_a.name} {self.get_rule_type_display()} {self.product_b.name}"
    
    class Meta:
        verbose_name = _("Compatibility Rule")
        verbose_name_plural = _("Compatibility Rules")
        ordering = ['name']
        indexes = [
            models.Index(fields=['product_a', 'product_b', 'rule_type']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['product_a', 'product_b', 'rule_type']
