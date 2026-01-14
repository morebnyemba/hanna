from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import uuid


class InstallationSystemRecord(models.Model):
    """
    Master object for tracking every installation throughout its lifecycle.
    Supports multiple installation types: Solar (SSI), Starlink (SLI), 
    Custom Furniture (CFI), and Hybrid Solar+Starlink (SSI).
    This generalizes the SSR concept to support all installation types.
    """
    
    class InstallationType(models.TextChoices):
        """
        Installation type choices based on InstallationRequest.INSTALLATION_TYPES.
        Excludes legacy 'residential' and 'commercial' values as those are now 
        captured in the system_classification field.
        """
        STARLINK = 'starlink', _('Starlink Installation')
        SOLAR = 'solar', _('Solar Panel Installation')
        HYBRID = 'hybrid', _('Hybrid (Starlink + Solar)')
        CUSTOM_FURNITURE = 'custom_furniture', _('Custom Furniture Installation')
    
    class SystemClassification(models.TextChoices):
        """System classification choices"""
        RESIDENTIAL = 'residential', _('Residential')
        COMMERCIAL = 'commercial', _('Commercial')
        HYBRID = 'hybrid', _('Hybrid')
    
    class CapacityUnit(models.TextChoices):
        """Capacity measurement units"""
        KW = 'kW', _('Kilowatts (kW)')
        MBPS = 'Mbps', _('Megabits per second (Mbps)')
        UNITS = 'units', _('Units')
    
    class InstallationStatus(models.TextChoices):
        """Installation status choices"""
        PENDING = 'pending', _('Pending')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMMISSIONED = 'commissioned', _('Commissioned')
        ACTIVE = 'active', _('Active')
        DECOMMISSIONED = 'decommissioned', _('Decommissioned')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    installation_request = models.OneToOneField(
        'customer_data.InstallationRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installation_system_record',
        help_text=_("The installation request that initiated this installation.")
    )
    customer = models.ForeignKey(
        'customer_data.CustomerProfile',
        on_delete=models.PROTECT,
        related_name='installation_system_records',
        help_text=_("The customer profile for this installation.")
    )
    order = models.ForeignKey(
        'customer_data.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='installation_system_records',
        help_text=_("The sales order associated with this installation.")
    )
    technicians = models.ManyToManyField(
        'warranty.Technician',
        related_name='installation_system_records',
        blank=True,
        help_text=_("The technician(s) assigned to this installation.")
    )
    installed_components = models.ManyToManyField(
        'products_and_services.SerializedItem',
        related_name='installation_system_records',
        blank=True,
        help_text=_("SerializedItems that are part of this installation.")
    )
    warranties = models.ManyToManyField(
        'warranty.Warranty',
        related_name='installation_system_records',
        blank=True,
        help_text=_("Warranties associated with this installation.")
    )
    job_cards = models.ManyToManyField(
        'customer_data.JobCard',
        related_name='installation_system_records',
        blank=True,
        help_text=_("Service job cards associated with this installation.")
    )
    
    # Installation details
    installation_type = models.CharField(
        _("Installation Type"),
        max_length=50,
        choices=InstallationType.choices,
        db_index=True,
        help_text=_("Type of installation (solar, starlink, hybrid, custom_furniture).")
    )
    system_size = models.DecimalField(
        _("System Size/Capacity"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("System size or capacity (e.g., kW for solar, Mbps for starlink).")
    )
    capacity_unit = models.CharField(
        _("Capacity Unit"),
        max_length=10,
        choices=CapacityUnit.choices,
        default=CapacityUnit.UNITS,
        help_text=_("Unit of measurement for system capacity.")
    )
    system_classification = models.CharField(
        _("System Classification"),
        max_length=20,
        choices=SystemClassification.choices,
        default=SystemClassification.RESIDENTIAL,
        db_index=True,
        help_text=_("Classification of the installation system.")
    )
    
    # Status and dates
    installation_status = models.CharField(
        _("Installation Status"),
        max_length=20,
        choices=InstallationStatus.choices,
        default=InstallationStatus.PENDING,
        db_index=True,
        help_text=_("Current status of the installation.")
    )
    installation_date = models.DateField(
        _("Installation Date"),
        null=True,
        blank=True,
        help_text=_("Date when the installation was performed.")
    )
    commissioning_date = models.DateField(
        _("Commissioning Date"),
        null=True,
        blank=True,
        help_text=_("Date when the system was commissioned and activated.")
    )
    
    # Monitoring and location
    remote_monitoring_id = models.CharField(
        _("Remote Monitoring ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("ID for remote monitoring system (e.g., solar monitoring portal).")
    )
    latitude = models.DecimalField(
        _("Latitude"),
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text=_("GPS latitude coordinate of the installation site.")
    )
    longitude = models.DecimalField(
        _("Longitude"),
        max_digits=10,
        decimal_places=7,
        null=True,
        blank=True,
        help_text=_("GPS longitude coordinate of the installation site.")
    )
    installation_address = models.TextField(
        _("Installation Address"),
        blank=True,
        null=True,
        help_text=_("Full address of the installation site.")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """
        Returns string representation: "ISR-{id} - {customer_name} - {installation_type} - {system_size}{unit}"
        Examples: 
        - "ISR-123 - John Doe - solar - 5kW"
        - "ISR-456 - Jane Smith - starlink - 100Mbps"
        - "ISR-789 - Bob Jones - custom_furniture - 3units"
        """
        customer_name = self.customer.get_full_name() or str(self.customer.contact.whatsapp_id)
        
        # Format system size with unit
        if self.system_size:
            size_str = f"{self.system_size}{self.capacity_unit}"
        else:
            size_str = "N/A"
        
        # Use first 8 characters of UUID for cleaner display
        short_id = str(self.id)[:8]
        
        return f"ISR-{short_id} - {customer_name} - {self.installation_type} - {size_str}"
    
    class Meta:
        verbose_name = _("Installation System Record")
        verbose_name_plural = _("Installation System Records")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['installation_type', 'installation_status']),
            models.Index(fields=['customer', 'installation_date']),
        ]
