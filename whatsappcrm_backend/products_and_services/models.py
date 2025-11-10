from django.db import models
from django.utils.translation import gettext_lazy as _

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
        IN_STOCK = 'in_stock', _('In Stock')
        SOLD = 'sold', _('Sold')
        IN_REPAIR = 'in_repair', _('In Repair')
        RETURNED = 'returned', _('Returned')
        DECOMMISSIONED = 'decommissioned', _('Decommissioned')

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
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=Status.choices,
        default=Status.IN_STOCK,
        db_index=True,
        help_text=_("The current status of this individual item.")
    )
    # You can add more fields here to track the item's lifecycle,
    # such as purchase_date, sale_date, etc.

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} (SN: {self.serial_number})"

    class Meta:
        verbose_name = _("Serialized Item")
        verbose_name_plural = _("Serialized Items")
        ordering = ['-created_at']
