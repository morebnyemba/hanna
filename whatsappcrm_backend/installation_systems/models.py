from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
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
    
    def clean(self):
        """
        Validate the model before saving.
        Prevent marking installation as COMMISSIONED without complete checklists.
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
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.clean()
        super().save(*args, **kwargs)
    
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
        
        percentage = (Decimal(completed_count) / Decimal(len(required_items))) * Decimal('100')
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
