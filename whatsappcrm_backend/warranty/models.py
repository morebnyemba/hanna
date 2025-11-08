from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid

class Manufacturer(models.Model):
    """
    Represents a product manufacturer.
    """
    name = models.CharField(_("Manufacturer Name"), max_length=255, unique=True)
    contact_email = models.EmailField(_("Contact Email"), max_length=254, blank=True, null=True)
    # Link to a user account for dashboard access
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='manufacturer_profile',
        help_text=_("The user account that can access this manufacturer's dashboard.")
    )

    def __str__(self):
        return self.name

class Technician(models.Model):
    class TechnicianType(models.TextChoices):
        INSTALLER = 'installer', _('Installer')
        FACTORY = 'factory', _('Factory')
        CALLOUT = 'callout', _('Callout')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='technician_profile'
    )
    technician_type = models.CharField(
        _("Technician Type"),
        max_length=20,
        choices=TechnicianType.choices,
        default=TechnicianType.INSTALLER
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='technicians',
        help_text=_("The manufacturer this technician is associated with (if any).")
    )
    specialization = models.CharField(_("Specialization"), max_length=255, blank=True, help_text="e.g., Solar, Plumbing, Electrical")
    contact_phone = models.CharField(_("Contact Phone"), max_length=20, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Installer(models.Model):
    technician = models.OneToOneField(
        Technician,
        on_delete=models.CASCADE,
        related_name='installer_profile'
    )

    def __str__(self):
        return self.technician.user.get_full_name() or self.technician.user.username

class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField()
    technician = models.ForeignKey(Technician, on_delete=models.CASCADE, related_name='events')

    def __str__(self):
        return self.title

class Warranty(models.Model):
    """
    Represents a warranty for a specific product purchased by a customer.
    """
    class WarrantyStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        EXPIRED = 'expired', _('Expired')
        VOID = 'void', _('Void')

    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.PROTECT, related_name='warranties', null=True, blank=True)
    serialized_item = models.OneToOneField(
        'products_and_services.SerializedItem',
        on_delete=models.CASCADE,
        related_name='warranty',
        help_text=_("The specific serialized item that this warranty covers.")
    )
    customer = models.ForeignKey('customer_data.CustomerProfile', on_delete=models.CASCADE, related_name='warranties')
    associated_order = models.ForeignKey('customer_data.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='warranties')
    start_date = models.DateField(_("Warranty Start Date"), default=timezone.now)
    end_date = models.DateField(_("Warranty End Date"))
    manufacturer_email = models.EmailField(_("Manufacturer Email"), max_length=254, blank=True, null=True, help_text=_("Email for sending warranty claim notifications to the product manufacturer."))
    status = models.CharField(_("Status"), max_length=20, choices=WarrantyStatus.choices, default=WarrantyStatus.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Warranty for {self.product.name} (SN: {self.product_serial_number})"

    class Meta:
        verbose_name = _("Warranty")
        verbose_name_plural = _("Warranties")
        ordering = ['-end_date']


class WarrantyClaim(models.Model):
    """
    Represents a claim made by a customer against a specific warranty.
    """
    class ClaimStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Review')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        REPLACED = 'replaced', _('Replaced')
        CLOSED = 'closed', _('Closed')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    warranty = models.ForeignKey(Warranty, on_delete=models.CASCADE, related_name='claims')
    claim_id = models.CharField(_("Claim ID"), max_length=20, unique=True, editable=False)
    description_of_fault = models.TextField(_("Description of Fault"))
    status = models.CharField(_("Claim Status"), max_length=20, choices=ClaimStatus.choices, default=ClaimStatus.PENDING, db_index=True)
    resolution_notes = models.TextField(_("Resolution Notes"), blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Claim {self.claim_id} for {self.warranty.product.name}"

    class Meta:
        verbose_name = _("Warranty Claim")
        verbose_name_plural = _("Warranty Claims")
        ordering = ['-created_at']


class TechnicianComment(models.Model):
    """
    A comment made by a technician on a JobCard or WarrantyClaim.
    """
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='technician_comments',
        limit_choices_to={'is_staff': True}
    )
    comment = models.TextField(_("Comment"))
    created_at = models.DateTimeField(auto_now_add=True)

    # Generic Foreign Key to link to either JobCard or WarrantyClaim
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=36) # To accommodate UUIDs and other PKs
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Comment by {self.technician} on {self.content_object} at {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        ordering = ['-created_at']