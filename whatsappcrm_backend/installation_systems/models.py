from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
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
    
    def are_all_checklists_complete(self):
        """
        Check if all required checklists are 100% complete.
        Returns tuple: (all_complete: bool, incomplete_checklists: list)
        """
        # Get all checklist entries for this installation
        entries = self.checklist_entries.all()
        
        if not entries.exists():
            # No checklists exist - may want to handle this case differently
            # For now, we allow completion if no checklists are assigned
            return True, []
        
        incomplete = []
        for entry in entries:
            if not entry.is_fully_completed():
                incomplete.append({
                    'template_name': entry.template.name,
                    'checklist_type': entry.template.get_checklist_type_display(),
                    'completion_percentage': float(entry.completion_percentage)
                })
        
        return len(incomplete) == 0, incomplete
    
    def get_required_photo_types(self):
        """
        Get list of required photo types for this installation.
        Returns list of photo types that must be uploaded.
        """
        # Define required photo types based on installation type
        required_photos = {
            'solar': ['serial_number', 'test_result', 'after'],
            'starlink': ['serial_number', 'equipment', 'after'],
            'hybrid': ['serial_number', 'test_result', 'equipment', 'after'],
            'custom_furniture': ['before', 'after'],
        }
        return required_photos.get(self.installation_type, [])
    
    def are_all_required_photos_uploaded(self):
        """
        Check if all required photo types have been uploaded.
        Returns tuple: (all_uploaded: bool, missing_photo_types: list)
        """
        required_types = self.get_required_photo_types()
        
        if not required_types:
            # No required photos for this installation type
            return True, []
        
        # Get all uploaded photo types
        uploaded_types = set(
            self.photos.values_list('photo_type', flat=True).distinct()
        )
        
        # Find missing photo types
        missing_types = [
            photo_type for photo_type in required_types
            if photo_type not in uploaded_types
        ]
        
        return len(missing_types) == 0, missing_types
    
    def clean(self):
        """
        Validate the model before saving.
        Prevent marking installation as COMMISSIONED without complete checklists and required photos.
        """
        # Only validate if status is being set to COMMISSIONED or ACTIVE
        if self.installation_status in [self.InstallationStatus.COMMISSIONED, self.InstallationStatus.ACTIVE]:
            # Check if we're actually changing the status (not on initial save)
            if self.pk:
                old_instance = InstallationSystemRecord.objects.filter(pk=self.pk).first()
                # Only validate if status is actually changing to COMMISSIONED/ACTIVE
                if old_instance and old_instance.installation_status not in [
                    self.InstallationStatus.COMMISSIONED, 
                    self.InstallationStatus.ACTIVE
                ]:
                    # Check checklists
                    all_complete, incomplete = self.are_all_checklists_complete()
                    if not all_complete:
                        incomplete_list = ', '.join([
                            f"{ic['template_name']} ({ic['completion_percentage']}%)"
                            for ic in incomplete
                        ])
                        raise ValidationError(
                            f"Cannot mark installation as {self.get_installation_status_display()} "
                            f"until all checklists are 100% complete. "
                            f"Incomplete checklists: {incomplete_list}"
                        )
                    
                    # Check required photos
                    photos_complete, missing_photos = self.are_all_required_photos_uploaded()
                    if not photos_complete:
                        # Format photo type names for display (capitalize and replace underscores)
                        missing_list = ', '.join([
                            photo_type.replace('_', ' ').title()
                            for photo_type in missing_photos
                        ])
                        raise ValidationError(
                            f"Cannot mark installation as {self.get_installation_status_display()} "
                            f"until all required photos are uploaded. "
                            f"Missing photo types: {missing_list}"
                        )
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def short_id(self):
        """Get shortened UUID for display (ISR-xxxxxxxx)"""
        return f"ISR-{str(self.id)[:8]}"
    
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


class CommissioningChecklistTemplate(models.Model):
    """
    Template for commissioning checklists.
    Defines the steps and requirements for different types of installations.
    """
    
    class ChecklistType(models.TextChoices):
        """Checklist type choices"""
        PRE_INSTALL = 'pre_install', _('Pre-Installation')
        INSTALLATION = 'installation', _('Installation')
        COMMISSIONING = 'commissioning', _('Commissioning')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Template details
    name = models.CharField(
        _("Template Name"),
        max_length=255,
        help_text=_("Name of the checklist template")
    )
    checklist_type = models.CharField(
        _("Checklist Type"),
        max_length=20,
        choices=ChecklistType.choices,
        db_index=True,
        help_text=_("Type of checklist (pre-install, installation, commissioning)")
    )
    installation_type = models.CharField(
        _("Installation Type"),
        max_length=50,
        choices=InstallationSystemRecord.InstallationType.choices,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Optional: Restrict template to specific installation type")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description of the checklist purpose and scope")
    )
    
    # Checklist items stored as JSON
    # Structure: [
    #   {
    #     "id": "item_1",
    #     "title": "Check site accessibility",
    #     "description": "Verify vehicle can access installation site",
    #     "required": true,
    #     "requires_photo": true,
    #     "photo_count": 2,
    #     "notes_required": false
    #   },
    #   ...
    # ]
    items = models.JSONField(
        _("Checklist Items"),
        default=list,
        help_text=_("JSON array of checklist items with requirements")
    )
    
    # Template status
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this template is active and available for use")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Returns string representation: "{name} ({checklist_type})" """
        return f"{self.name} ({self.get_checklist_type_display()})"
    
    class Meta:
        verbose_name = _("Commissioning Checklist Template")
        verbose_name_plural = _("Commissioning Checklist Templates")
        ordering = ['checklist_type', 'name']
        indexes = [
            models.Index(fields=['checklist_type', 'installation_type']),
            models.Index(fields=['is_active', 'checklist_type']),
        ]


class InstallationChecklistEntry(models.Model):
    """
    Record of a completed or in-progress checklist for an installation.
    Tracks which items have been completed and stores associated data.
    """
    
    class CompletionStatus(models.TextChoices):
        """Completion status choices"""
        NOT_STARTED = 'not_started', _('Not Started')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    installation_record = models.ForeignKey(
        InstallationSystemRecord,
        on_delete=models.CASCADE,
        related_name='checklist_entries',
        help_text=_("The installation system record this checklist belongs to")
    )
    template = models.ForeignKey(
        CommissioningChecklistTemplate,
        on_delete=models.PROTECT,
        related_name='checklist_entries',
        help_text=_("The template this checklist is based on")
    )
    technician = models.ForeignKey(
        'warranty.Technician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_checklists',
        help_text=_("The technician who completed this checklist")
    )
    
    # Completion data stored as JSON
    # Structure: {
    #   "item_1": {
    #     "completed": true,
    #     "completed_at": "2024-01-15T10:30:00Z",
    #     "notes": "Site access confirmed",
    #     "photos": ["uuid1", "uuid2"],  # References to media files
    #     "completed_by": "technician_id"
    #   },
    #   ...
    # }
    completed_items = models.JSONField(
        _("Completed Items"),
        default=dict,
        help_text=_("JSON object tracking completion status of each item")
    )
    
    # Status tracking
    completion_status = models.CharField(
        _("Completion Status"),
        max_length=20,
        choices=CompletionStatus.choices,
        default=CompletionStatus.NOT_STARTED,
        db_index=True,
        help_text=_("Overall completion status of the checklist")
    )
    completion_percentage = models.DecimalField(
        _("Completion Percentage"),
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_("Percentage of required items completed (0-100)")
    )
    
    # Timestamps
    started_at = models.DateTimeField(
        _("Started At"),
        null=True,
        blank=True,
        help_text=_("When the checklist was first started")
    )
    completed_at = models.DateTimeField(
        _("Completed At"),
        null=True,
        blank=True,
        help_text=_("When the checklist was fully completed")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_completion_percentage(self):
        """
        Calculate completion percentage based on required items.
        Returns percentage as Decimal (0-100).
        """
        if not self.template.items:
            return Decimal('0')
        
        required_items = [item for item in self.template.items if item.get('required', False)]
        if not required_items:
            return Decimal('100')
        
        completed_count = 0
        for item in required_items:
            item_id = item.get('id')
            if item_id and item_id in self.completed_items:
                if self.completed_items[item_id].get('completed', False):
                    completed_count += 1
        
        # Safety check to prevent division by zero (though should never occur)
        total_required = len(required_items)
        if total_required == 0:
            return Decimal('100')
        
        percentage = (Decimal(completed_count) / Decimal(total_required)) * Decimal('100')
        return percentage.quantize(Decimal('0.01'))
    
    def update_completion_status(self):
        """
        Update the completion status and percentage.
        Should be called after modifying completed_items.
        """
        self.completion_percentage = self.calculate_completion_percentage()
        
        if self.completion_percentage == Decimal('0'):
            self.completion_status = self.CompletionStatus.NOT_STARTED
            self.started_at = None
        elif self.completion_percentage < Decimal('100'):
            self.completion_status = self.CompletionStatus.IN_PROGRESS
            if not self.started_at:
                self.started_at = timezone.now()
        else:
            self.completion_status = self.CompletionStatus.COMPLETED
            if not self.completed_at:
                self.completed_at = timezone.now()
    
    def is_fully_completed(self):
        """
        Check if all required items are completed.
        Returns True if 100% complete, False otherwise.
        """
        return self.completion_percentage == Decimal('100')
    
    def __str__(self):
        """Returns string representation"""
        return f"{self.template.name} - {self.installation_record} ({self.completion_percentage}%)"
    
    class Meta:
        verbose_name = _("Installation Checklist Entry")
        verbose_name_plural = _("Installation Checklist Entries")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['installation_record', 'template']),
            models.Index(fields=['completion_status', 'completion_percentage']),
        ]


class InstallationPhoto(models.Model):
    """
    Stores photos uploaded during installation process.
    Photos are linked to installation records and can be categorized by type.
    Used for commissioning evidence and installation reports.
    """
    
    class PhotoType(models.TextChoices):
        """Photo type choices for categorizing installation photos"""
        BEFORE = 'before', _('Before Installation')
        DURING = 'during', _('During Installation')
        AFTER = 'after', _('After Installation')
        SERIAL_NUMBER = 'serial_number', _('Serial Number')
        TEST_RESULT = 'test_result', _('Test Result')
        SITE = 'site', _('Site Photo')
        EQUIPMENT = 'equipment', _('Equipment Photo')
        OTHER = 'other', _('Other')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    installation_record = models.ForeignKey(
        InstallationSystemRecord,
        on_delete=models.CASCADE,
        related_name='photos',
        help_text=_("The installation system record this photo belongs to")
    )
    media_asset = models.ForeignKey(
        'media_manager.MediaAsset',
        on_delete=models.CASCADE,
        related_name='installation_photos',
        help_text=_("The media asset containing the actual photo file")
    )
    checklist_item = models.CharField(
        _("Checklist Item ID"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Optional: ID of the checklist item this photo is linked to")
    )
    uploaded_by = models.ForeignKey(
        'warranty.Technician',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_photos',
        help_text=_("The technician who uploaded this photo")
    )
    
    # Photo metadata
    photo_type = models.CharField(
        _("Photo Type"),
        max_length=20,
        choices=PhotoType.choices,
        db_index=True,
        help_text=_("Category/type of the photo")
    )
    caption = models.CharField(
        _("Caption"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Short caption or title for the photo")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        null=True,
        help_text=_("Detailed description of what the photo shows")
    )
    is_required = models.BooleanField(
        _("Is Required"),
        default=False,
        help_text=_("Whether this photo type is required for commissioning")
    )
    
    # Timestamps
    uploaded_at = models.DateTimeField(
        _("Uploaded At"),
        auto_now_add=True,
        help_text=_("When the photo was uploaded")
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Returns string representation"""
        return f"{self.get_photo_type_display()} - {self.installation_record} ({self.uploaded_at.strftime('%Y-%m-%d')})"
    
    class Meta:
        verbose_name = _("Installation Photo")
        verbose_name_plural = _("Installation Photos")
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['installation_record', 'photo_type']),
            models.Index(fields=['photo_type', 'is_required']),
            models.Index(fields=['uploaded_by', 'uploaded_at']),
        ]


class PayoutConfiguration(models.Model):
    """
    Configuration for installer payout rates.
    Defines how technicians are paid based on system size and installation type.
    """
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Configuration details
    name = models.CharField(
        _("Configuration Name"),
        max_length=255,
        help_text=_("Descriptive name for this payout configuration")
    )
    installation_type = models.CharField(
        _("Installation Type"),
        max_length=50,
        choices=InstallationSystemRecord.InstallationType.choices,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Installation type this rate applies to (leave blank for all types)")
    )
    
    # Size-based rate tiers
    min_system_size = models.DecimalField(
        _("Minimum System Size"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Minimum system size for this rate tier (null means no minimum)")
    )
    max_system_size = models.DecimalField(
        _("Maximum System Size"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Maximum system size for this rate tier (null means no maximum)")
    )
    capacity_unit = models.CharField(
        _("Capacity Unit"),
        max_length=10,
        choices=InstallationSystemRecord.CapacityUnit.choices,
        default=InstallationSystemRecord.CapacityUnit.UNITS,
        help_text=_("Unit of measurement for system capacity")
    )
    
    # Payout rates
    rate_type = models.CharField(
        _("Rate Type"),
        max_length=20,
        choices=[
            ('flat', _('Flat Rate')),
            ('per_unit', _('Per Unit Rate')),
            ('percentage', _('Percentage of Order Value')),
        ],
        default='flat',
        help_text=_("How the payout amount is calculated")
    )
    rate_amount = models.DecimalField(
        _("Rate Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Amount for flat rate, per unit rate, or percentage")
    )
    
    # Quality metrics (future enhancement)
    quality_bonus_enabled = models.BooleanField(
        _("Quality Bonus Enabled"),
        default=False,
        help_text=_("Enable quality-based bonuses for this configuration")
    )
    quality_bonus_amount = models.DecimalField(
        _("Quality Bonus Amount"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Bonus amount for meeting quality metrics")
    )
    
    # Configuration status
    is_active = models.BooleanField(
        _("Is Active"),
        default=True,
        help_text=_("Whether this configuration is active and should be used")
    )
    priority = models.IntegerField(
        _("Priority"),
        default=0,
        help_text=_("Higher priority configurations are applied first (0 is lowest)")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        """Returns string representation"""
        size_range = ""
        if self.min_system_size or self.max_system_size:
            min_val = f"{self.min_system_size}" if self.min_system_size else "0"
            max_val = f"{self.max_system_size}" if self.max_system_size else "∞"
            size_range = f" ({min_val}-{max_val}{self.capacity_unit})"
        return f"{self.name}{size_range} - ${self.rate_amount} ({self.rate_type})"
    
    class Meta:
        verbose_name = _("Payout Configuration")
        verbose_name_plural = _("Payout Configurations")
        ordering = ['-priority', 'installation_type', 'min_system_size']
        indexes = [
            models.Index(fields=['installation_type', 'is_active']),
            models.Index(fields=['is_active', 'priority']),
        ]


class InstallerPayout(models.Model):
    """
    Represents a payout to a technician for completed installations.
    Tracks the approval workflow and payment status.
    """
    
    class PayoutStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        PAID = 'paid', _('Paid')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    technician = models.ForeignKey(
        'warranty.Technician',
        on_delete=models.PROTECT,
        related_name='payouts',
        help_text=_("The technician receiving this payout")
    )
    installations = models.ManyToManyField(
        InstallationSystemRecord,
        related_name='payouts',
        help_text=_("Installation system records included in this payout")
    )
    configuration = models.ForeignKey(
        PayoutConfiguration,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payouts',
        help_text=_("The payout configuration used for calculation")
    )
    
    # Payout details
    payout_amount = models.DecimalField(
        _("Payout Amount"),
        max_digits=10,
        decimal_places=2,
        help_text=_("Total amount to be paid to the technician")
    )
    calculation_method = models.TextField(
        _("Calculation Method"),
        blank=True,
        help_text=_("Description of how the payout amount was calculated")
    )
    calculation_breakdown = models.JSONField(
        _("Calculation Breakdown"),
        default=dict,
        blank=True,
        help_text=_("Detailed breakdown of payout calculation")
    )
    
    # Status tracking
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING,
        db_index=True,
        help_text=_("Current status of the payout")
    )
    
    # Notes and comments
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Additional notes or comments about this payout")
    )
    admin_notes = models.TextField(
        _("Admin Notes"),
        blank=True,
        help_text=_("Internal notes for admins (not visible to technician)")
    )
    rejection_reason = models.TextField(
        _("Rejection Reason"),
        blank=True,
        help_text=_("Reason for rejection if status is REJECTED")
    )
    
    # Approval workflow
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_payouts',
        help_text=_("Admin user who approved this payout")
    )
    approved_at = models.DateTimeField(
        _("Approved At"),
        null=True,
        blank=True,
        help_text=_("When the payout was approved")
    )
    
    # Payment tracking
    paid_at = models.DateTimeField(
        _("Paid At"),
        null=True,
        blank=True,
        help_text=_("When the payment was made")
    )
    payment_reference = models.CharField(
        _("Payment Reference"),
        max_length=255,
        blank=True,
        help_text=_("Payment reference number or transaction ID")
    )
    
    # Zoho integration
    zoho_bill_id = models.CharField(
        _("Zoho Bill ID"),
        max_length=255,
        blank=True,
        help_text=_("ID of the bill/expense created in Zoho")
    )
    zoho_sync_status = models.CharField(
        _("Zoho Sync Status"),
        max_length=50,
        blank=True,
        help_text=_("Status of synchronization with Zoho")
    )
    zoho_sync_error = models.TextField(
        _("Zoho Sync Error"),
        blank=True,
        help_text=_("Error message if Zoho sync failed")
    )
    zoho_synced_at = models.DateTimeField(
        _("Zoho Synced At"),
        null=True,
        blank=True,
        help_text=_("When the payout was synced to Zoho")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def short_id(self):
        """Get shortened UUID for display (PAY-xxxxxxxx)"""
        return f"PAY-{str(self.id)[:8]}"
    
    def __str__(self):
        """Returns string representation"""
        return f"{self.short_id} - {self.technician} - ${self.payout_amount} ({self.get_status_display()})"
    
    class Meta:
        verbose_name = _("Installer Payout")
        verbose_name_plural = _("Installer Payouts")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['technician', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['approved_by', 'approved_at']),
        ]
