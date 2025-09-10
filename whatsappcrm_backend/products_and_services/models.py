from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
# Create your models here.
class OfferingCategory(models.Model):
    """
    A category for organizing software products and professional services.
    Supports nested categories.
    """
    name = models.CharField(_("Category Name"), max_length=255, unique=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text=_("Parent category for creating a hierarchy (e.g., 'Software' -> 'Accounting').")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Offering Category")
        verbose_name_plural = _("Offering Categories")
        ordering = ['name']

class SoftwareProduct(models.Model):
    """
    Represents a software product, which could be SaaS or a licensed application.
    """
    class LicenseType(models.TextChoices):
        SUBSCRIPTION = 'subscription', _('Subscription')
        PERPETUAL = 'perpetual', _('Perpetual License')
        ONE_TIME = 'one_time', _('One-Time Purchase')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Software Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    sku = models.CharField(_("SKU / Product Code"), max_length=100, unique=True, blank=True, null=True)
    category = models.ForeignKey(
        OfferingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='software_products'
    )
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    license_type = models.CharField(_("License Type"), max_length=20, choices=LicenseType.choices, default=LicenseType.SUBSCRIPTION)
    is_saas = models.BooleanField(_("Is SaaS Product"), default=True, help_text=_("Is this a cloud-based Software-as-a-Service?"))
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this software is available for sale.")
    )
    version = models.CharField(_("Current Version"), max_length=20, blank=True, null=True)
    image = models.ImageField(_("Product Logo/Icon"), upload_to='software_products/', blank=True, null=True)
    dedicated_flow_name = models.CharField(
        _("Dedicated Flow Name"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_(
            "The name of the flow to trigger for specific follow-up on this product."
        ),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"

    class Meta:
        verbose_name = _("Software Product")
        verbose_name_plural = _("Software Products")
        ordering = ['name']

class ProfessionalService(models.Model):
    """
    Represents a professional service like accounting, consulting, or registration.
    """
    class BillingCycle(models.TextChoices):
        ONE_TIME = 'one_time', _('One-Time')
        HOURLY = 'hourly', _('Hourly')
        MONTHLY = 'monthly', _('Monthly')
        RETAINER = 'retainer', _('Retainer')
        PROJECT_BASED = 'project_based', _('Project-Based')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Service Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    category = models.ForeignKey(
        OfferingCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='professional_services'
    )
    price = models.DecimalField(_("Price / Rate"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    billing_cycle = models.CharField(
        _("Billing Cycle"),
        max_length=20,
        choices=BillingCycle.choices,
        default=BillingCycle.PROJECT_BASED
    )
    is_active = models.BooleanField(_("Is Active"), default=True, help_text=_("Whether the service is currently offered."))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()})"

    class Meta:
        verbose_name = _("Professional Service")
        verbose_name_plural = _("Professional Services")
        ordering = ['name']

class SoftwareModule(models.Model):
    """
    Represents a specific module or add-on for a core SoftwareProduct.
    e.g., 'Accounting Module', 'Fiscalization Module'.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        SoftwareProduct,
        on_delete=models.CASCADE,
        related_name='modules',
        help_text=_("The core software product this module belongs to.")
    )
    name = models.CharField(_("Module Name"), max_length=255)
    description = models.TextField(_("Description"), blank=True, null=True)
    sku = models.CharField(_("SKU / Module Code"), max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2, help_text=_("Price for this module, often added to the base product price."))
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    is_active = models.BooleanField(default=True, help_text=_("Is this module available for sale?"))
    compatible_devices = models.ManyToManyField('Device', blank=True, related_name='compatible_modules')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    class Meta:
        verbose_name = _("Software Module")
        verbose_name_plural = _("Software Modules")
        ordering = ['product', 'name']

class Device(models.Model):
    """
    Represents a physical hardware device that can be sold with software.
    e.g., Fiscal printers, POS terminals, barcode scanners.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("Device Name"), max_length=255)
    manufacturer = models.CharField(_("Manufacturer"), max_length=100, blank=True, null=True)
    model_number = models.CharField(_("Model Number"), max_length=100, blank=True, null=True)
    sku = models.CharField(_("SKU / Part Number"), max_length=100, unique=True, blank=True, null=True)
    description = models.TextField(_("Description"), blank=True, null=True)
    price = models.DecimalField(_("Price"), max_digits=12, decimal_places=2)
    currency = models.CharField(_("Currency"), max_length=3, default='USD')
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this device is available for sale.")
    )
    image = models.ImageField(_("Device Image"), upload_to='devices/', blank=True, null=True,
                              help_text=_("An image of the hardware device. Requires the 'Pillow' library."))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.manufacturer} {self.model_number or ''})".strip()

    class Meta:
        verbose_name = _("Hardware Device")
        verbose_name_plural = _("Hardware Devices")
        ordering = ['name']
