"""
Django Admin configuration for Solar Integration models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    DailyEnergyStats,
    InverterDataPoint,
    SolarAlert,
    SolarAPICredential,
    SolarInverter,
    SolarInverterBrand,
    SolarStation,
)


@admin.register(SolarInverterBrand)
class SolarInverterBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'api_base_url', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    ordering = ['name']


@admin.register(SolarAPICredential)
class SolarAPICredentialAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'account_id', 'sync_status_badge', 'is_active', 'last_sync_at']
    list_filter = ['brand', 'sync_status', 'is_active']
    search_fields = ['name', 'account_id']
    readonly_fields = ['id', 'created_at', 'updated_at', 'last_sync_at', 'sync_status', 'sync_error']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'brand', 'is_active')
        }),
        ('API Credentials', {
            'fields': ('api_key', 'api_secret', 'account_id', 'station_id'),
            'classes': ('collapse',),
        }),
        ('Token Information', {
            'fields': ('access_token', 'refresh_token', 'token_expires_at'),
            'classes': ('collapse',),
        }),
        ('Sync Status', {
            'fields': ('sync_status', 'last_sync_at', 'sync_error'),
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    def sync_status_badge(self, obj):
        colors = {
            'pending': 'gray',
            'syncing': 'blue',
            'success': 'green',
            'error': 'red',
        }
        color = colors.get(obj.sync_status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.sync_status.upper()
        )
    sync_status_badge.short_description = 'Sync Status'


@admin.register(SolarStation)
class SolarStationAdmin(admin.ModelAdmin):
    list_display = ['name', 'credential', 'status_badge', 'total_capacity_kw', 'customer', 'last_data_time']
    list_filter = ['status', 'is_active', 'credential__brand']
    search_fields = ['name', 'external_id', 'address']
    readonly_fields = ['id', 'external_id', 'created_at', 'updated_at', 'last_data_time']
    raw_id_fields = ['customer']
    
    def status_badge(self, obj):
        colors = {
            'online': 'green',
            'offline': 'red',
            'warning': 'orange',
            'fault': 'red',
            'unknown': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'


class InverterDataPointInline(admin.TabularInline):
    model = InverterDataPoint
    extra = 0
    readonly_fields = ['timestamp', 'power_w', 'battery_soc', 'grid_voltage_v', 'status']
    max_num = 10
    ordering = ['-timestamp']


@admin.register(SolarInverter)
class SolarInverterAdmin(admin.ModelAdmin):
    list_display = [
        'serial_number', 'model', 'station', 'status_badge', 
        'current_power_w', 'battery_soc_percent', 'today_energy_kwh', 'last_data_time'
    ]
    list_filter = ['status', 'is_active', 'station__credential__brand']
    search_fields = ['serial_number', 'external_id', 'model']
    readonly_fields = [
        'id', 'external_id', 'created_at', 'updated_at', 'last_data_time',
        'current_power_w', 'today_energy_kwh', 'total_energy_kwh',
        'grid_voltage_v', 'grid_frequency_hz',
        'pv1_voltage_v', 'pv1_current_a', 'pv1_power_w',
        'pv2_voltage_v', 'pv2_current_a', 'pv2_power_w',
        'battery_voltage_v', 'battery_current_a', 'battery_power_w',
        'battery_soc_percent', 'battery_temperature_c',
        'load_power_w', 'grid_power_w', 'inverter_temperature_c',
    ]
    inlines = [InverterDataPointInline]
    
    fieldsets = (
        (None, {
            'fields': ('station', 'serial_number', 'model', 'status', 'is_active')
        }),
        ('Specifications', {
            'fields': ('rated_power_kw', 'firmware_version'),
        }),
        ('Current Readings', {
            'fields': (
                'current_power_w', 'today_energy_kwh', 'total_energy_kwh',
                'grid_voltage_v', 'grid_frequency_hz',
            ),
        }),
        ('PV Input', {
            'fields': (
                ('pv1_voltage_v', 'pv1_current_a', 'pv1_power_w'),
                ('pv2_voltage_v', 'pv2_current_a', 'pv2_power_w'),
            ),
            'classes': ('collapse',),
        }),
        ('Battery', {
            'fields': (
                'battery_voltage_v', 'battery_current_a', 'battery_power_w',
                'battery_soc_percent', 'battery_temperature_c',
            ),
            'classes': ('collapse',),
        }),
        ('Load & Grid', {
            'fields': ('load_power_w', 'grid_power_w', 'inverter_temperature_c'),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('id', 'external_id', 'last_data_time', 'created_at', 'updated_at', 'metadata'),
            'classes': ('collapse',),
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'online': 'green',
            'offline': 'red',
            'standby': 'blue',
            'warning': 'orange',
            'fault': 'red',
            'unknown': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'


@admin.register(InverterDataPoint)
class InverterDataPointAdmin(admin.ModelAdmin):
    list_display = ['inverter', 'timestamp', 'power_w', 'battery_soc', 'grid_voltage_v', 'status']
    list_filter = ['inverter__station', 'timestamp']
    search_fields = ['inverter__serial_number']
    readonly_fields = ['inverter', 'timestamp', 'raw_data']
    date_hierarchy = 'timestamp'


@admin.register(DailyEnergyStats)
class DailyEnergyStatsAdmin(admin.ModelAdmin):
    list_display = [
        'inverter', 'date', 'energy_generated_kwh', 'energy_consumed_kwh',
        'energy_imported_kwh', 'energy_exported_kwh', 'estimated_savings'
    ]
    list_filter = ['inverter__station', 'date']
    search_fields = ['inverter__serial_number']
    date_hierarchy = 'date'


@admin.register(SolarAlert)
class SolarAlertAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'alert_type', 'severity_badge', 'station', 'inverter',
        'is_active', 'acknowledged', 'resolved', 'occurred_at'
    ]
    list_filter = ['alert_type', 'severity', 'is_active', 'acknowledged', 'resolved']
    search_fields = ['title', 'description', 'code']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'acknowledged_at', 'acknowledged_by',
        'resolved_at', 'notification_sent_at'
    ]
    raw_id_fields = ['station', 'inverter']
    date_hierarchy = 'occurred_at'
    
    actions = ['mark_acknowledged', 'mark_resolved']
    
    def severity_badge(self, obj):
        colors = {
            'info': 'blue',
            'warning': 'orange',
            'error': 'red',
            'critical': 'darkred',
        }
        color = colors.get(obj.severity, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.severity.upper()
        )
    severity_badge.short_description = 'Severity'
    
    @admin.action(description='Mark selected alerts as acknowledged')
    def mark_acknowledged(self, request, queryset):
        for alert in queryset:
            alert.acknowledge(user=request.user)
        self.message_user(request, f'{queryset.count()} alerts acknowledged.')
    
    @admin.action(description='Mark selected alerts as resolved')
    def mark_resolved(self, request, queryset):
        for alert in queryset:
            alert.resolve(notes=f'Bulk resolved by {request.user}')
        self.message_user(request, f'{queryset.count()} alerts resolved.')
