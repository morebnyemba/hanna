"""
Solar System Monitoring Integration Models

This module provides models for integrating with solar inverter monitoring systems,
starting with Deye inverters. It supports real-time data collection, historical
analytics, and alert management for solar installations.
"""

import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class SolarInverterBrand(models.Model):
    """Supported solar inverter brands/manufacturers."""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, help_text="Short code for API identification")
    api_base_url = models.URLField(blank=True, null=True, help_text="Base URL for the brand's cloud API")
    api_version = models.CharField(max_length=20, blank=True, default="v1")
    is_active = models.BooleanField(default=True)
    logo_url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solar Inverter Brand"
        verbose_name_plural = "Solar Inverter Brands"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SolarAPICredential(models.Model):
    """API credentials for connecting to solar monitoring platforms."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(
        SolarInverterBrand, 
        on_delete=models.CASCADE,
        related_name='credentials'
    )
    name = models.CharField(max_length=100, help_text="Friendly name for this credential set")
    
    # Authentication fields - encrypted at rest in production
    api_key = models.CharField(max_length=500, blank=True, help_text="API key for cloud authentication")
    api_secret = models.CharField(max_length=500, blank=True, help_text="API secret/password")
    access_token = models.TextField(blank=True, help_text="OAuth access token if applicable")
    refresh_token = models.TextField(blank=True, help_text="OAuth refresh token if applicable")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Connection settings
    account_id = models.CharField(max_length=100, blank=True, help_text="Account/User ID on the platform")
    station_id = models.CharField(max_length=100, blank=True, help_text="Station/Plant ID if applicable")
    
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('syncing', 'Syncing'),
            ('success', 'Success'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    sync_error = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solar API Credential"
        verbose_name_plural = "Solar API Credentials"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.brand.name})"
    
    def is_token_expired(self):
        """Check if the access token has expired."""
        if not self.token_expires_at:
            return True
        return timezone.now() >= self.token_expires_at


class SolarStation(models.Model):
    """
    Represents a solar power station/plant installation.
    A station can have multiple inverters and other equipment.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    credential = models.ForeignKey(
        SolarAPICredential,
        on_delete=models.CASCADE,
        related_name='stations'
    )
    
    # Station identification
    external_id = models.CharField(max_length=100, help_text="ID from the monitoring platform")
    name = models.CharField(max_length=200)
    
    # Location
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    timezone_name = models.CharField(max_length=50, default='UTC')
    
    # System specifications
    total_capacity_kw = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total installed capacity in kW"
    )
    installation_date = models.DateField(null=True, blank=True)
    
    # Current status
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('warning', 'Warning'),
            ('fault', 'Fault'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    last_data_time = models.DateTimeField(null=True, blank=True)
    
    # Link to customer if applicable
    customer = models.ForeignKey(
        'customer_data.CustomerProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solar_stations'
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional station metadata from API")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solar Station"
        verbose_name_plural = "Solar Stations"
        ordering = ['-created_at']
        unique_together = [['credential', 'external_id']]
    
    def __str__(self):
        return f"{self.name} ({self.total_capacity_kw or 'N/A'} kW)"


class SolarInverter(models.Model):
    """
    Individual solar inverter device within a station.
    Tracks real-time and historical performance data.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey(
        SolarStation,
        on_delete=models.CASCADE,
        related_name='inverters'
    )
    
    # Device identification
    external_id = models.CharField(max_length=100, help_text="Device ID from the monitoring platform")
    serial_number = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    
    # Specifications
    rated_power_kw = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Rated power output in kW"
    )
    firmware_version = models.CharField(max_length=50, blank=True)
    
    # Current status
    status = models.CharField(
        max_length=20,
        choices=[
            ('online', 'Online'),
            ('offline', 'Offline'),
            ('standby', 'Standby'),
            ('warning', 'Warning'),
            ('fault', 'Fault'),
            ('unknown', 'Unknown'),
        ],
        default='unknown'
    )
    
    # Latest readings (snapshot for quick access)
    current_power_w = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Current power output in Watts"
    )
    today_energy_kwh = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Energy generated today in kWh"
    )
    total_energy_kwh = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Total lifetime energy generated in kWh"
    )
    
    # Grid parameters
    grid_voltage_v = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    grid_frequency_hz = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # DC input (from solar panels)
    pv1_voltage_v = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pv1_current_a = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pv1_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pv2_voltage_v = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pv2_current_a = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pv2_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Battery (for hybrid inverters)
    battery_voltage_v = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    battery_current_a = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    battery_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    battery_soc_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Battery state of charge percentage"
    )
    battery_temperature_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Load consumption
    load_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Grid import/export
    grid_power_w = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Positive = importing from grid, Negative = exporting to grid"
    )
    
    # Temperature
    inverter_temperature_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    last_data_time = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional device metadata")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Solar Inverter"
        verbose_name_plural = "Solar Inverters"
        ordering = ['station', 'serial_number']
        unique_together = [['station', 'external_id']]
    
    def __str__(self):
        return f"{self.model or 'Inverter'} - {self.serial_number or self.external_id}"


class InverterDataPoint(models.Model):
    """
    Time-series data points for inverter performance tracking.
    Used for historical analysis, charts, and reporting.
    """
    
    inverter = models.ForeignKey(
        SolarInverter,
        on_delete=models.CASCADE,
        related_name='data_points'
    )
    timestamp = models.DateTimeField(db_index=True)
    
    # Power readings
    power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    pv_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    load_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    grid_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    battery_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Energy readings (cumulative for the day)
    energy_kwh = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True)
    
    # Battery
    battery_soc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Grid
    grid_voltage_v = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    grid_frequency_hz = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Temperature
    temperature_c = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    
    # Status at this point in time
    status = models.CharField(max_length=20, blank=True)
    
    # Full raw data from API
    raw_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Inverter Data Point"
        verbose_name_plural = "Inverter Data Points"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['inverter', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
        # Prevent duplicate entries for same inverter/timestamp
        unique_together = [['inverter', 'timestamp']]
    
    def __str__(self):
        return f"{self.inverter} @ {self.timestamp}"


class DailyEnergyStats(models.Model):
    """
    Aggregated daily energy statistics for reporting and analytics.
    Pre-computed to improve dashboard performance.
    """
    
    inverter = models.ForeignKey(
        SolarInverter,
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )
    date = models.DateField(db_index=True)
    
    # Generation
    energy_generated_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    peak_power_w = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    generation_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Consumption
    energy_consumed_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    
    # Grid interaction
    energy_imported_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    energy_exported_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    
    # Battery
    battery_charged_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    battery_discharged_kwh = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    
    # Performance metrics
    self_consumption_ratio = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Percentage of generated energy consumed on-site"
    )
    self_sufficiency_ratio = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Percentage of consumption met by solar"
    )
    
    # Financial (estimated)
    estimated_savings = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Estimated cost savings in local currency"
    )
    
    # Environmental impact
    co2_avoided_kg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Estimated CO2 emissions avoided in kg"
    )
    
    class Meta:
        verbose_name = "Daily Energy Stats"
        verbose_name_plural = "Daily Energy Stats"
        ordering = ['-date']
        unique_together = [['inverter', 'date']]
    
    def __str__(self):
        return f"{self.inverter} - {self.date}"


class SolarAlert(models.Model):
    """
    Alerts and notifications for solar system events.
    Can be triggered by faults, performance issues, or maintenance needs.
    """
    
    class Severity(models.TextChoices):
        INFO = 'info', 'Information'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        CRITICAL = 'critical', 'Critical'
    
    class AlertType(models.TextChoices):
        FAULT = 'fault', 'Fault/Error'
        OFFLINE = 'offline', 'Device Offline'
        LOW_PRODUCTION = 'low_production', 'Low Production'
        GRID_FAILURE = 'grid_failure', 'Grid Failure'
        BATTERY_LOW = 'battery_low', 'Battery Low'
        OVERTEMPERATURE = 'overtemperature', 'Over Temperature'
        MAINTENANCE = 'maintenance', 'Maintenance Required'
        COMMUNICATION = 'communication', 'Communication Error'
        OTHER = 'other', 'Other'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Can be associated with station, inverter, or both
    station = models.ForeignKey(
        SolarStation,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    inverter = models.ForeignKey(
        SolarInverter,
        on_delete=models.CASCADE,
        related_name='alerts',
        null=True,
        blank=True
    )
    
    # Alert details
    alert_type = models.CharField(max_length=20, choices=AlertType.choices)
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.WARNING)
    code = models.CharField(max_length=50, blank=True, help_text="Error/fault code from inverter")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Status tracking
    is_active = models.BooleanField(default=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_solar_alerts'
    )
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    # Notification tracking
    notification_sent = models.BooleanField(default=False)
    notification_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    occurred_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        verbose_name = "Solar Alert"
        verbose_name_plural = "Solar Alerts"
        ordering = ['-occurred_at']
        indexes = [
            models.Index(fields=['is_active', 'severity']),
            models.Index(fields=['station', 'is_active']),
            models.Index(fields=['inverter', 'is_active']),
        ]
    
    def __str__(self):
        return f"[{self.severity}] {self.title}"
    
    def acknowledge(self, user=None):
        """Mark the alert as acknowledged."""
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save(update_fields=['acknowledged', 'acknowledged_at', 'acknowledged_by', 'updated_at'])
    
    def resolve(self, notes=""):
        """Mark the alert as resolved."""
        self.resolved = True
        self.resolved_at = timezone.now()
        self.resolution_notes = notes
        self.is_active = False
        self.save(update_fields=['resolved', 'resolved_at', 'resolution_notes', 'is_active', 'updated_at'])
