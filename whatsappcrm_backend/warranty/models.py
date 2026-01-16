from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid


def get_current_date():
    """Helper function for DateField default to avoid lambda serialization issues in migrations"""
    return timezone.now().date()

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
    start_date = models.DateField(_("Warranty Start Date"), default=get_current_date)
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


class WarrantyRule(models.Model):
    """
    Configurable warranty rules for automatic duration assignment.
    Links warranty duration to specific products or product categories.
    """
    name = models.CharField(_("Rule Name"), max_length=255, help_text=_("Descriptive name for this warranty rule"))
    product = models.ForeignKey(
        'products_and_services.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='warranty_rules',
        help_text=_("Specific product this rule applies to (leave blank if using category)")
    )
    product_category = models.ForeignKey(
        'products_and_services.ProductCategory',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='warranty_rules',
        help_text=_("Product category this rule applies to (leave blank if using specific product)")
    )
    warranty_duration_days = models.PositiveIntegerField(
        _("Warranty Duration (Days)"),
        help_text=_("Number of days the warranty is valid for")
    )
    terms_and_conditions = models.TextField(
        _("Terms and Conditions"),
        blank=True,
        null=True,
        help_text=_("Specific terms and conditions for this warranty rule")
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Whether this rule is currently active and should be applied")
    )
    priority = models.PositiveIntegerField(
        _("Priority"),
        default=0,
        help_text=_("Higher priority rules are applied first (0 is lowest)")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        target = self.product.name if self.product else (self.product_category.name if self.product_category else "General")
        return f"{self.name} - {target} ({self.warranty_duration_days} days)"

    class Meta:
        verbose_name = _("Warranty Rule")
        verbose_name_plural = _("Warranty Rules")
        ordering = ['-priority', '-created_at']

    def clean(self):
        """Ensure either product or category is set, not both"""
        from django.core.exceptions import ValidationError
        if self.product and self.product_category:
            raise ValidationError(_("A warranty rule cannot apply to both a specific product and a category. Choose one."))
        if not self.product and not self.product_category:
            raise ValidationError(_("A warranty rule must apply to either a specific product or a product category."))


class SLAThreshold(models.Model):
    """
    Service Level Agreement thresholds for different request types.
    Defines response and resolution time expectations.
    """
    class RequestType(models.TextChoices):
        INSTALLATION = 'installation', _('Installation Request')
        SERVICE = 'service', _('Service Request')
        WARRANTY_CLAIM = 'warranty_claim', _('Warranty Claim')
        SITE_ASSESSMENT = 'site_assessment', _('Site Assessment')

    name = models.CharField(_("SLA Name"), max_length=255, help_text=_("Descriptive name for this SLA threshold"))
    request_type = models.CharField(
        _("Request Type"),
        max_length=50,
        choices=RequestType.choices,
        db_index=True,
        help_text=_("Type of request this SLA applies to")
    )
    response_time_hours = models.PositiveIntegerField(
        _("Response Time (Hours)"),
        help_text=_("Maximum hours for initial response to customer")
    )
    resolution_time_hours = models.PositiveIntegerField(
        _("Resolution Time (Hours)"),
        help_text=_("Maximum hours for complete resolution")
    )
    escalation_rules = models.TextField(
        _("Escalation Rules"),
        blank=True,
        null=True,
        help_text=_("JSON or text describing escalation procedures when SLA is breached")
    )
    notification_threshold_percent = models.PositiveIntegerField(
        _("Notification Threshold (%)"),
        default=80,
        help_text=_("Send alerts when this percentage of time has elapsed (e.g., 80 for 80%)")
    )
    is_active = models.BooleanField(
        _("Active"),
        default=True,
        help_text=_("Whether this SLA threshold is currently active")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.get_request_type_display()} (Response: {self.response_time_hours}h, Resolution: {self.resolution_time_hours}h)"

    class Meta:
        verbose_name = _("SLA Threshold")
        verbose_name_plural = _("SLA Thresholds")
        ordering = ['request_type', 'name']
        unique_together = [['request_type', 'name']]


class SLAStatus(models.Model):
    """
    Tracks SLA compliance status for individual requests.
    Stores calculated SLA metrics and violation flags.
    """
    class StatusType(models.TextChoices):
        COMPLIANT = 'compliant', _('Compliant')
        WARNING = 'warning', _('Warning - Approaching Deadline')
        BREACHED = 'breached', _('SLA Breached')

    # Generic Foreign Key to support different request types
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=36)  # To accommodate UUIDs and other PKs
    content_object = GenericForeignKey('content_type', 'object_id')

    sla_threshold = models.ForeignKey(
        SLAThreshold,
        on_delete=models.PROTECT,
        related_name='sla_statuses',
        help_text=_("The SLA threshold being tracked")
    )
    
    request_created_at = models.DateTimeField(_("Request Created At"))
    response_time_deadline = models.DateTimeField(_("Response Deadline"))
    resolution_time_deadline = models.DateTimeField(_("Resolution Deadline"))
    
    response_completed_at = models.DateTimeField(_("Response Completed At"), null=True, blank=True)
    resolution_completed_at = models.DateTimeField(_("Resolution Completed At"), null=True, blank=True)
    
    response_status = models.CharField(
        _("Response Status"),
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.COMPLIANT
    )
    resolution_status = models.CharField(
        _("Resolution Status"),
        max_length=20,
        choices=StatusType.choices,
        default=StatusType.COMPLIANT
    )
    
    last_notification_sent = models.DateTimeField(_("Last Notification Sent"), null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SLA Status for {self.content_object} - Response: {self.response_status}, Resolution: {self.resolution_status}"

    class Meta:
        verbose_name = _("SLA Status")
        verbose_name_plural = _("SLA Statuses")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['response_status']),
            models.Index(fields=['resolution_status']),
        ]

    def _calculate_status_from_deadline(self, now, deadline, completed_at):
        """
        Calculate status based on deadline and completion time.
        
        Args:
            now: Current datetime
            deadline: Deadline datetime
            completed_at: Completion datetime (nullable)
            
        Returns:
            StatusType enum value
        """
        if completed_at:
            # Task completed - check if it was on time
            if completed_at <= deadline:
                return self.StatusType.COMPLIANT
            else:
                return self.StatusType.BREACHED
        else:
            # Task not completed yet - check deadline
            if now > deadline:
                return self.StatusType.BREACHED
            else:
                # Check if approaching deadline (based on notification threshold)
                time_elapsed = (now - self.request_created_at).total_seconds()
                time_allowed = (deadline - self.request_created_at).total_seconds()
                # Avoid division by zero
                if time_allowed > 0 and time_elapsed / time_allowed >= (self.sla_threshold.notification_threshold_percent / 100):
                    return self.StatusType.WARNING
                else:
                    return self.StatusType.COMPLIANT

    def update_status(self):
        """Update SLA status based on current time"""
        now = timezone.now()
        
        # Update response status
        self.response_status = self._calculate_status_from_deadline(
            now, 
            self.response_time_deadline, 
            self.response_completed_at
        )
        
        # Update resolution status
        self.resolution_status = self._calculate_status_from_deadline(
            now,
            self.resolution_time_deadline,
            self.resolution_completed_at
        )
        
        self.save()

    def should_send_notification(self):
        """Check if notification should be sent"""
        if self.response_status == self.StatusType.WARNING or self.resolution_status == self.StatusType.WARNING:
            # Only send if not sent recently (within last hour)
            if not self.last_notification_sent or (timezone.now() - self.last_notification_sent).total_seconds() > 3600:
                return True
        elif self.response_status == self.StatusType.BREACHED or self.resolution_status == self.StatusType.BREACHED:
            # Always notify on breach if not sent in last 4 hours
            if not self.last_notification_sent or (timezone.now() - self.last_notification_sent).total_seconds() > 14400:
                return True
        return False