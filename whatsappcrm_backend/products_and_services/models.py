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
    
    # Meta sync tracking fields
    meta_sync_attempts = models.PositiveIntegerField(_("Meta Sync Attempts"), default=0, help_text=_("Number of times sync to Meta Catalog has been attempted"))
    meta_sync_last_error = models.TextField(_("Last Meta Sync Error"), blank=True, null=True, help_text=_("Last error message from Meta API sync attempt"))
    meta_sync_last_attempt = models.DateTimeField(_("Last Meta Sync Attempt"), blank=True, null=True, help_text=_("Timestamp of last sync attempt"))
    meta_sync_last_success = models.DateTimeField(_("Last Meta Sync Success"), blank=True, null=True, help_text=_("Timestamp of last successful sync"))
    
    # --- Inventory ---
    stock_quantity = models.PositiveIntegerField(_("Stock Quantity"), default=0, help_text=_("The number of items available in stock. Used for WhatsApp Catalog inventory management."))
    
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

    class Meta:
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
        ordering = ['name']


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
        """Total price of all items in the cart"""
        return sum(item.subtotal for item in self.items.all())

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
