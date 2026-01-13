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


class SystemBundle(models.Model):
    """
    Represents a pre-configured installation package for various installation types.
    Can include solar packages, Starlink packages, custom furniture packages, or hybrid bundles.
    """
    
    class InstallationType(models.TextChoices):
        """Installation type choices matching InstallationRequest.INSTALLATION_TYPES"""
        SOLAR = 'solar', _('Solar Panel Installation')
        STARLINK = 'starlink', _('Starlink Installation')
        CUSTOM_FURNITURE = 'custom_furniture', _('Custom Furniture Installation')
        HYBRID = 'hybrid', _('Hybrid (Solar + Starlink)')
    
    class BundleClassification(models.TextChoices):
        """Bundle classification choices"""
        RESIDENTIAL = 'residential', _('Residential')
        COMMERCIAL = 'commercial', _('Commercial')
        HYBRID = 'hybrid', _('Hybrid')
    
    class CapacityUnit(models.TextChoices):
        """Capacity measurement units"""
        KW = 'kW', _('Kilowatts (kW)')
        MBPS = 'Mbps', _('Megabits per second (Mbps)')
        UNITS = 'units', _('Units')
    
    # Basic Information
    name = models.CharField(
        _("Bundle Name"),
        max_length=255,
        help_text=_("Name of the bundle (e.g., '3kW Residential Solar Kit', 'Starlink Business Kit')")
    )
    sku = models.CharField(
        _("SKU/Code"),
        max_length=100,
        unique=True,
        help_text=_("Unique SKU or product code for this bundle")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Detailed description of the bundle and what's included")
    )
    image = models.ImageField(
        _("Bundle Image"),
        upload_to='bundle_images/',
        blank=True,
        null=True,
        help_text=_("Image representing the bundle")
    )
    
    # Installation and Classification
    installation_type = models.CharField(
        _("Installation Type"),
        max_length=50,
        choices=InstallationType.choices,
        db_index=True,
        help_text=_("Type of installation this bundle is for")
    )
    bundle_classification = models.CharField(
        _("Bundle Classification"),
        max_length=20,
        choices=BundleClassification.choices,
        db_index=True,
        help_text=_("Classification of the bundle (residential, commercial, hybrid)")
    )
    
    # Capacity Information
    system_capacity = models.DecimalField(
        _("System Capacity"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("System capacity value (e.g., 3.0 for 3kW solar, 150 for 150Mbps Starlink)")
    )
    capacity_unit = models.CharField(
        _("Capacity Unit"),
        max_length=10,
        choices=CapacityUnit.choices,
        default=CapacityUnit.UNITS,
        help_text=_("Unit of measurement for system capacity")
    )
    
    # Pricing
    total_price = models.DecimalField(
        _("Total Price"),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Total price of the bundle. If not set, calculated from component prices.")
    )
    currency = models.CharField(
        _("Currency"),
        max_length=3,
        default='USD',
        help_text=_("Currency code (e.g., USD, ZWL)")
    )
    
    # Status
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        db_index=True,
        help_text=_("Whether this bundle is available for sale")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def get_calculated_price(self):
        """Calculate total price from components if not manually set."""
        if self.total_price is not None:
            return self.total_price
        
        from decimal import Decimal
        total = Decimal('0.00')
        for component in self.components.all():
            if component.product.price:
                total += component.product.price * component.quantity
        return total
    
    def get_total_price(self):
        """Get the total price (either manual or calculated)."""
        return self.get_calculated_price()
    
    def are_all_components_in_stock(self):
        """Check if all required components are in stock."""
        for component in self.components.filter(is_required=True):
            if component.product.stock_quantity < component.quantity:
                return False
        return True
    
    def validate_bundle_components(self):
        """
        Validate that the bundle has the required components based on installation type.
        Returns tuple (is_valid, error_messages)
        """
        errors = []
        components = self.components.all()
        
        # Get product types for validation
        component_types = [c.product.product_type for c in components]
        
        if self.installation_type == self.InstallationType.SOLAR:
            # Solar bundles need: inverter, battery, and solar panel
            required_keywords = ['inverter', 'battery', 'panel']
            component_names = [c.product.name.lower() for c in components]
            
            for keyword in required_keywords:
                if not any(keyword in name for name in component_names):
                    errors.append(f"Solar bundle must include at least one {keyword}")
        
        elif self.installation_type == self.InstallationType.STARLINK:
            # Starlink bundles need: router and dish
            required_keywords = ['router', 'dish']
            component_names = [c.product.name.lower() for c in components]
            
            for keyword in required_keywords:
                if not any(keyword in name for name in component_names):
                    errors.append(f"Starlink bundle must include at least one {keyword}")
        
        elif self.installation_type == self.InstallationType.CUSTOM_FURNITURE:
            # Custom furniture needs at least one furniture piece
            if not components.exists():
                errors.append("Custom furniture bundle must include at least one furniture piece")
        
        elif self.installation_type == self.InstallationType.HYBRID:
            # Hybrid bundles need both solar and starlink components
            component_names = [c.product.name.lower() for c in components]
            
            # Check for solar components
            has_solar = any(keyword in ' '.join(component_names) for keyword in ['inverter', 'battery', 'panel'])
            # Check for starlink components
            has_starlink = any(keyword in ' '.join(component_names) for keyword in ['router', 'dish'])
            
            if not has_solar:
                errors.append("Hybrid bundle must include solar components (inverter, battery, panel)")
            if not has_starlink:
                errors.append("Hybrid bundle must include starlink components (router, dish)")
        
        return (len(errors) == 0, errors)
    
    def save(self, *args, **kwargs):
        """Generate SKU if not provided."""
        if not self.sku:
            # Generate SKU based on installation type and classification
            prefix = self.installation_type[:3].upper()
            classification = self.bundle_classification[:3].upper()
            import uuid
            unique_id = uuid.uuid4().hex[:6].upper()
            self.sku = f"{prefix}-{classification}-{unique_id}"
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _("System Bundle")
        verbose_name_plural = _("System Bundles")
        ordering = ['name']
        indexes = [
            models.Index(fields=['installation_type', 'is_active']),
            models.Index(fields=['bundle_classification', 'is_active']),
        ]


class BundleComponent(models.Model):
    """
    Represents a product component within a system bundle.
    Links products to bundles with quantity and requirement information.
    """
    
    bundle = models.ForeignKey(
        SystemBundle,
        on_delete=models.CASCADE,
        related_name='components',
        help_text=_("The bundle this component belongs to")
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='bundle_inclusions',
        help_text=_("The product included in this bundle")
    )
    quantity = models.PositiveIntegerField(
        _("Quantity"),
        default=1,
        help_text=_("Number of units of this product in the bundle")
    )
    is_required = models.BooleanField(
        _("Is Required"),
        default=True,
        help_text=_("Whether this component is mandatory for the bundle")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.bundle.name}"
    
    @property
    def component_price(self):
        """Calculate the price for this component (quantity * unit price)."""
        if self.product.price:
            return self.product.price * self.quantity
        return 0
    
    @property
    def is_in_stock(self):
        """Check if this component has sufficient stock."""
        return self.product.stock_quantity >= self.quantity
    
    class Meta:
        verbose_name = _("Bundle Component")
        verbose_name_plural = _("Bundle Components")
        ordering = ['bundle', '-is_required', 'product__name']
        unique_together = ['bundle', 'product']
