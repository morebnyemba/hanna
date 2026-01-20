"""
Serializers for Solar Integration API.
"""

from rest_framework import serializers

from .models import (
    DailyEnergyStats,
    InverterDataPoint,
    SolarAlert,
    SolarAPICredential,
    SolarInverter,
    SolarInverterBrand,
    SolarStation,
)


class SolarInverterBrandSerializer(serializers.ModelSerializer):
    """Serializer for solar inverter brands."""
    
    class Meta:
        model = SolarInverterBrand
        fields = [
            'id', 'name', 'code', 'api_base_url', 'api_version',
            'is_active', 'logo_url', 'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SolarAPICredentialSerializer(serializers.ModelSerializer):
    """Serializer for API credentials - hides sensitive data."""
    
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    
    class Meta:
        model = SolarAPICredential
        fields = [
            'id', 'brand', 'brand_name', 'name', 'account_id', 'station_id',
            'is_active', 'sync_status', 'last_sync_at', 'sync_error',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sync_status', 'last_sync_at', 'sync_error', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Hide sensitive fields in responses."""
        data = super().to_representation(instance)
        # Never expose tokens or secrets in API responses
        return data


class SolarAPICredentialCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating API credentials."""
    
    class Meta:
        model = SolarAPICredential
        fields = [
            'id', 'brand', 'name', 'api_key', 'api_secret',
            'account_id', 'station_id', 'is_active'
        ]
        extra_kwargs = {
            'api_key': {'write_only': True},
            'api_secret': {'write_only': True},
        }


class SolarStationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for station list views."""
    
    brand_name = serializers.CharField(source='credential.brand.name', read_only=True)
    inverter_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = SolarStation
        fields = [
            'id', 'name', 'external_id', 'brand_name', 'status',
            'total_capacity_kw', 'address', 'last_data_time',
            'inverter_count', 'is_active'
        ]


class SolarStationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for station detail views."""
    
    brand_name = serializers.CharField(source='credential.brand.name', read_only=True)
    customer_name = serializers.CharField(source='customer.contact.name', read_only=True, allow_null=True)
    inverters = serializers.SerializerMethodField()
    active_alerts = serializers.SerializerMethodField()
    
    class Meta:
        model = SolarStation
        fields = [
            'id', 'name', 'external_id', 'brand_name', 'status',
            'address', 'latitude', 'longitude', 'timezone_name',
            'total_capacity_kw', 'installation_date', 'last_data_time',
            'customer', 'customer_name', 'metadata',
            'inverters', 'active_alerts',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'external_id', 'created_at', 'updated_at']
    
    def get_inverters(self, obj):
        """Get list of inverters for this station."""
        return SolarInverterListSerializer(obj.inverters.all(), many=True).data
    
    def get_active_alerts(self, obj):
        """Get active alerts for this station."""
        alerts = obj.alerts.filter(is_active=True)[:5]
        return SolarAlertListSerializer(alerts, many=True).data


class SolarInverterListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for inverter list views."""
    
    station_name = serializers.CharField(source='station.name', read_only=True)
    
    class Meta:
        model = SolarInverter
        fields = [
            'id', 'serial_number', 'model', 'station_name', 'status',
            'rated_power_kw', 'current_power_w', 'today_energy_kwh',
            'battery_soc_percent', 'last_data_time', 'is_active'
        ]


class SolarInverterDetailSerializer(serializers.ModelSerializer):
    """Full serializer for inverter detail views."""
    
    station_name = serializers.CharField(source='station.name', read_only=True)
    brand_name = serializers.CharField(source='station.credential.brand.name', read_only=True)
    active_alerts = serializers.SerializerMethodField()
    
    class Meta:
        model = SolarInverter
        fields = [
            'id', 'station', 'station_name', 'brand_name',
            'external_id', 'serial_number', 'model', 'status',
            'rated_power_kw', 'firmware_version',
            # Current readings
            'current_power_w', 'today_energy_kwh', 'total_energy_kwh',
            'grid_voltage_v', 'grid_frequency_hz',
            # PV inputs
            'pv1_voltage_v', 'pv1_current_a', 'pv1_power_w',
            'pv2_voltage_v', 'pv2_current_a', 'pv2_power_w',
            # Battery
            'battery_voltage_v', 'battery_current_a', 'battery_power_w',
            'battery_soc_percent', 'battery_temperature_c',
            # Load & Grid
            'load_power_w', 'grid_power_w', 'inverter_temperature_c',
            # Metadata
            'last_data_time', 'metadata', 'active_alerts',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'external_id', 'created_at', 'updated_at']
    
    def get_active_alerts(self, obj):
        """Get active alerts for this inverter."""
        alerts = obj.alerts.filter(is_active=True)[:5]
        return SolarAlertListSerializer(alerts, many=True).data


class InverterDataPointSerializer(serializers.ModelSerializer):
    """Serializer for time-series data points."""
    
    class Meta:
        model = InverterDataPoint
        fields = [
            'timestamp', 'power_w', 'pv_power_w', 'load_power_w',
            'grid_power_w', 'battery_power_w', 'energy_kwh',
            'battery_soc', 'grid_voltage_v', 'grid_frequency_hz',
            'temperature_c', 'status'
        ]


class DailyEnergyStatsSerializer(serializers.ModelSerializer):
    """Serializer for daily energy statistics."""
    
    inverter_serial = serializers.CharField(source='inverter.serial_number', read_only=True)
    
    class Meta:
        model = DailyEnergyStats
        fields = [
            'inverter', 'inverter_serial', 'date',
            'energy_generated_kwh', 'peak_power_w', 'generation_hours',
            'energy_consumed_kwh',
            'energy_imported_kwh', 'energy_exported_kwh',
            'battery_charged_kwh', 'battery_discharged_kwh',
            'self_consumption_ratio', 'self_sufficiency_ratio',
            'estimated_savings', 'co2_avoided_kg'
        ]


class SolarAlertListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for alert list views."""
    
    station_name = serializers.CharField(source='station.name', read_only=True, allow_null=True)
    inverter_serial = serializers.CharField(source='inverter.serial_number', read_only=True, allow_null=True)
    
    class Meta:
        model = SolarAlert
        fields = [
            'id', 'alert_type', 'severity', 'title', 'code',
            'station_name', 'inverter_serial',
            'is_active', 'acknowledged', 'resolved', 'occurred_at'
        ]


class SolarAlertDetailSerializer(serializers.ModelSerializer):
    """Full serializer for alert detail views."""
    
    station_name = serializers.CharField(source='station.name', read_only=True, allow_null=True)
    inverter_serial = serializers.CharField(source='inverter.serial_number', read_only=True, allow_null=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = SolarAlert
        fields = [
            'id', 'station', 'station_name', 'inverter', 'inverter_serial',
            'alert_type', 'severity', 'code', 'title', 'description',
            'is_active', 'acknowledged', 'acknowledged_at', 'acknowledged_by', 'acknowledged_by_name',
            'resolved', 'resolved_at', 'resolution_notes',
            'notification_sent', 'notification_sent_at',
            'occurred_at', 'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'acknowledged_at', 'acknowledged_by', 'resolved_at',
            'notification_sent', 'notification_sent_at', 'created_at', 'updated_at'
        ]


class SolarDashboardSerializer(serializers.Serializer):
    """Serializer for solar dashboard summary data."""
    
    total_stations = serializers.IntegerField()
    total_inverters = serializers.IntegerField()
    online_inverters = serializers.IntegerField()
    offline_inverters = serializers.IntegerField()
    
    total_capacity_kw = serializers.DecimalField(max_digits=15, decimal_places=2)
    current_power_w = serializers.DecimalField(max_digits=15, decimal_places=2)
    today_energy_kwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    month_energy_kwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_energy_kwh = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    active_alerts = serializers.IntegerField()
    critical_alerts = serializers.IntegerField()
    
    co2_avoided_kg = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
    estimated_savings = serializers.DecimalField(max_digits=15, decimal_places=2, allow_null=True)
