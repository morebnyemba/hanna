# whatsappcrm_backend/installation_systems/branch_models.py
"""
Models for branch installer allocation and scheduling.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid


class InstallerAssignment(models.Model):
    """
    Links an installation to a specific installer with scheduling information.
    Allows branches to assign and schedule installers.
    """
    
    class AssignmentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        CONFIRMED = 'confirmed', _('Confirmed')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    installation_record = models.ForeignKey(
        'installation_systems.InstallationSystemRecord',
        on_delete=models.CASCADE,
        related_name='installer_assignments',
        help_text=_("The installation this assignment is for")
    )
    installer = models.ForeignKey(
        'warranty.Technician',
        on_delete=models.CASCADE,
        related_name='installer_assignments',
        help_text=_("The installer/technician assigned")
    )
    branch = models.ForeignKey(
        'users.RetailerBranch',
        on_delete=models.CASCADE,
        related_name='installer_assignments',
        null=True,
        blank=True,
        help_text=_("The branch that made this assignment")
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assignments_created',
        help_text=_("User who created this assignment")
    )
    
    # Scheduling
    scheduled_date = models.DateField(
        _("Scheduled Date"),
        help_text=_("Date when installation is scheduled")
    )
    scheduled_start_time = models.TimeField(
        _("Scheduled Start Time"),
        null=True,
        blank=True,
        help_text=_("Scheduled start time for installation")
    )
    scheduled_end_time = models.TimeField(
        _("Scheduled End Time"),
        null=True,
        blank=True,
        help_text=_("Estimated end time for installation")
    )
    estimated_duration_hours = models.DecimalField(
        _("Estimated Duration (hours)"),
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_("Estimated duration in hours")
    )
    
    # Status and tracking
    status = models.CharField(
        _("Assignment Status"),
        max_length=20,
        choices=AssignmentStatus.choices,
        default=AssignmentStatus.PENDING,
        db_index=True,
        help_text=_("Current status of this assignment")
    )
    
    # Actual completion tracking
    actual_start_time = models.DateTimeField(
        _("Actual Start Time"),
        null=True,
        blank=True,
        help_text=_("When installer actually started work")
    )
    actual_end_time = models.DateTimeField(
        _("Actual End Time"),
        null=True,
        blank=True,
        help_text=_("When installer actually completed work")
    )
    
    # Notes and feedback
    notes = models.TextField(
        _("Assignment Notes"),
        blank=True,
        help_text=_("Notes about this assignment")
    )
    completion_notes = models.TextField(
        _("Completion Notes"),
        blank=True,
        help_text=_("Notes added upon completion")
    )
    customer_feedback = models.TextField(
        _("Customer Feedback"),
        blank=True,
        help_text=_("Customer feedback after installation")
    )
    customer_satisfaction_rating = models.IntegerField(
        _("Customer Satisfaction Rating"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_("Customer satisfaction rating (1-5)")
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        _("Completed At"),
        null=True,
        blank=True,
        help_text=_("When the assignment was marked complete")
    )
    
    @property
    def actual_duration_hours(self):
        """Calculate actual duration if start and end times are set"""
        if self.actual_start_time and self.actual_end_time:
            delta = self.actual_end_time - self.actual_start_time
            return Decimal(delta.total_seconds() / 3600).quantize(Decimal('0.1'))
        return None
    
    @property
    def is_overdue(self):
        """Check if scheduled date has passed and not completed"""
        if self.status in [self.AssignmentStatus.COMPLETED, self.AssignmentStatus.CANCELLED]:
            return False
        return self.scheduled_date < timezone.now().date()
    
    def __str__(self):
        return f"{self.installer} → {self.installation_record.short_id} ({self.scheduled_date})"
    
    class Meta:
        verbose_name = _("Installer Assignment")
        verbose_name_plural = _("Installer Assignments")
        ordering = ['-scheduled_date', '-created_at']
        indexes = [
            models.Index(fields=['installer', 'scheduled_date']),
            models.Index(fields=['installation_record', 'status']),
            models.Index(fields=['branch', 'scheduled_date']),
            models.Index(fields=['status', 'scheduled_date']),
        ]


class InstallerAvailability(models.Model):
    """
    Tracks installer availability for scheduling purposes.
    Allows marking time blocks as available/unavailable.
    """
    
    class AvailabilityType(models.TextChoices):
        AVAILABLE = 'available', _('Available')
        UNAVAILABLE = 'unavailable', _('Unavailable')
        LEAVE = 'leave', _('Leave')
        SICK = 'sick', _('Sick Leave')
        TRAINING = 'training', _('Training')
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    installer = models.ForeignKey(
        'warranty.Technician',
        on_delete=models.CASCADE,
        related_name='availability_records',
        help_text=_("The installer this availability record is for")
    )
    
    # Date range
    date = models.DateField(
        _("Date"),
        db_index=True,
        help_text=_("Date of this availability record")
    )
    start_time = models.TimeField(
        _("Start Time"),
        null=True,
        blank=True,
        help_text=_("Start time for this availability block")
    )
    end_time = models.TimeField(
        _("End Time"),
        null=True,
        blank=True,
        help_text=_("End time for this availability block")
    )
    
    # Availability details
    availability_type = models.CharField(
        _("Availability Type"),
        max_length=20,
        choices=AvailabilityType.choices,
        default=AvailabilityType.AVAILABLE,
        help_text=_("Type of availability")
    )
    notes = models.TextField(
        _("Notes"),
        blank=True,
        help_text=_("Notes about this availability record")
    )
    
    # Tracking
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='availability_records_created',
        help_text=_("User who created this record")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        time_str = ""
        if self.start_time and self.end_time:
            time_str = f" ({self.start_time}-{self.end_time})"
        return f"{self.installer} - {self.date}{time_str} - {self.get_availability_type_display()}"
    
    class Meta:
        verbose_name = _("Installer Availability")
        verbose_name_plural = _("Installer Availability Records")
        ordering = ['-date', 'start_time']
        indexes = [
            models.Index(fields=['installer', 'date']),
            models.Index(fields=['date', 'availability_type']),
        ]
        unique_together = [['installer', 'date', 'start_time', 'end_time']]
