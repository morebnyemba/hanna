"""
Views for Solar Integration API.
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    DailyEnergyStats,
    InverterDataPoint,
    SolarAlert,
    SolarAPICredential,
    SolarInverter,
    SolarInverterBrand,
    SolarStation,
)
from .serializers import (
    DailyEnergyStatsSerializer,
    InverterDataPointSerializer,
    SolarAlertDetailSerializer,
    SolarAlertListSerializer,
    SolarAPICredentialCreateSerializer,
    SolarAPICredentialSerializer,
    SolarDashboardSerializer,
    SolarInverterBrandSerializer,
    SolarInverterDetailSerializer,
    SolarInverterListSerializer,
    SolarStationDetailSerializer,
    SolarStationListSerializer,
)
from .services import SolarServiceFactory

logger = logging.getLogger(__name__)


class SolarInverterBrandViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for listing supported inverter brands."""
    
    queryset = SolarInverterBrand.objects.filter(is_active=True)
    serializer_class = SolarInverterBrandSerializer
    permission_classes = [permissions.IsAuthenticated]


class SolarAPICredentialViewSet(viewsets.ModelViewSet):
    """ViewSet for managing API credentials."""
    
    queryset = SolarAPICredential.objects.all().select_related('brand')
    permission_classes = [permissions.IsAdminUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SolarAPICredentialCreateSerializer
        return SolarAPICredentialSerializer
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """Manually trigger a sync for this credential."""
        credential = self.get_object()
        service = SolarServiceFactory.get_service(credential)
        
        if not service:
            return Response(
                {'error': f'No service implementation for brand: {credential.brand.name}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, message = service.sync_all()
        
        return Response({
            'success': success,
            'message': message,
            'sync_status': credential.sync_status,
            'last_sync_at': credential.last_sync_at,
        })
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test the API connection for this credential."""
        credential = self.get_object()
        service = SolarServiceFactory.get_service(credential)
        
        if not service:
            return Response(
                {'error': f'No service implementation for brand: {credential.brand.name}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            success = service.authenticate()
            return Response({
                'success': success,
                'message': 'Connection successful' if success else 'Authentication failed',
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e),
            })


class SolarStationViewSet(viewsets.ModelViewSet):
    """ViewSet for solar stations."""
    
    queryset = SolarStation.objects.all().select_related(
        'credential', 'credential__brand', 'customer', 'customer__contact'
    ).annotate(inverter_count=Count('inverters'))
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SolarStationDetailSerializer
        return SolarStationListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by brand
        brand = self.request.query_params.get('brand')
        if brand:
            queryset = queryset.filter(credential__brand__code=brand)
        
        # Filter by active only
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset


class SolarInverterViewSet(viewsets.ModelViewSet):
    """ViewSet for solar inverters."""
    
    queryset = SolarInverter.objects.all().select_related(
        'station', 'station__credential', 'station__credential__brand'
    )
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SolarInverterDetailSerializer
        return SolarInverterListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by station
        station_id = self.request.query_params.get('station')
        if station_id:
            queryset = queryset.filter(station_id=station_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get historical data points for an inverter."""
        inverter = self.get_object()
        
        # Parse date range (default to last 24 hours)
        try:
            hours = int(request.query_params.get('hours', 24))
            hours = min(hours, 168)  # Max 1 week
        except ValueError:
            hours = 24
        
        start_time = timezone.now() - timedelta(hours=hours)
        
        data_points = InverterDataPoint.objects.filter(
            inverter=inverter,
            timestamp__gte=start_time
        ).order_by('timestamp')
        
        serializer = InverterDataPointSerializer(data_points, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def daily_stats(self, request, pk=None):
        """Get daily statistics for an inverter."""
        inverter = self.get_object()
        
        # Parse date range (default to last 30 days)
        try:
            days = int(request.query_params.get('days', 30))
            days = min(days, 365)  # Max 1 year
        except ValueError:
            days = 30
        
        start_date = timezone.now().date() - timedelta(days=days)
        
        stats = DailyEnergyStats.objects.filter(
            inverter=inverter,
            date__gte=start_date
        ).order_by('date')
        
        serializer = DailyEnergyStatsSerializer(stats, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def refresh(self, request, pk=None):
        """Refresh real-time data for this inverter."""
        inverter = self.get_object()
        credential = inverter.station.credential
        
        service = SolarServiceFactory.get_service(credential)
        if not service:
            return Response(
                {'error': 'No service implementation available'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            data = service.get_inverter_realtime_data(inverter.external_id)
            if data:
                service._update_inverter_realtime(inverter, data)
                inverter.refresh_from_db()
                return Response(SolarInverterDetailSerializer(inverter).data)
            else:
                return Response(
                    {'error': 'Failed to get real-time data'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        except Exception as e:
            logger.error(f"Error refreshing inverter {inverter.id}: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SolarAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for solar alerts."""
    
    queryset = SolarAlert.objects.all().select_related('station', 'inverter', 'acknowledged_by')
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SolarAlertDetailSerializer
        return SolarAlertListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by active only (default)
        if self.request.query_params.get('show_all') != 'true':
            queryset = queryset.filter(is_active=True)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        # Filter by alert type
        alert_type = self.request.query_params.get('type')
        if alert_type:
            queryset = queryset.filter(alert_type=alert_type)
        
        # Filter by station
        station_id = self.request.query_params.get('station')
        if station_id:
            queryset = queryset.filter(station_id=station_id)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge an alert."""
        alert = self.get_object()
        alert.acknowledge(user=request.user)
        return Response(SolarAlertDetailSerializer(alert).data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve an alert."""
        alert = self.get_object()
        notes = request.data.get('notes', '')
        alert.resolve(notes=notes)
        return Response(SolarAlertDetailSerializer(alert).data)


class SolarDashboardView(APIView):
    """API view for solar system dashboard summary."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get dashboard summary data."""
        
        # Get counts
        total_stations = SolarStation.objects.filter(is_active=True).count()
        total_inverters = SolarInverter.objects.filter(is_active=True).count()
        online_inverters = SolarInverter.objects.filter(
            is_active=True, status='online'
        ).count()
        offline_inverters = SolarInverter.objects.filter(
            is_active=True, status='offline'
        ).count()
        
        # Get capacity and power
        capacity_sum = SolarStation.objects.filter(
            is_active=True
        ).aggregate(total=Sum('total_capacity_kw'))['total'] or Decimal('0')
        
        power_sum = SolarInverter.objects.filter(
            is_active=True, status='online'
        ).aggregate(total=Sum('current_power_w'))['total'] or Decimal('0')
        
        today_energy = SolarInverter.objects.filter(
            is_active=True
        ).aggregate(total=Sum('today_energy_kwh'))['total'] or Decimal('0')
        
        total_energy = SolarInverter.objects.filter(
            is_active=True
        ).aggregate(total=Sum('total_energy_kwh'))['total'] or Decimal('0')
        
        # Get month energy from daily stats
        first_of_month = timezone.now().date().replace(day=1)
        month_energy = DailyEnergyStats.objects.filter(
            date__gte=first_of_month
        ).aggregate(total=Sum('energy_generated_kwh'))['total'] or Decimal('0')
        
        # Get alerts
        active_alerts = SolarAlert.objects.filter(is_active=True).count()
        critical_alerts = SolarAlert.objects.filter(
            is_active=True, severity='critical'
        ).count()
        
        # Estimated environmental and financial impact
        # Using standard conversion factors
        co2_per_kwh = Decimal('0.5')  # kg CO2 avoided per kWh
        price_per_kwh = Decimal('0.15')  # USD per kWh (can be configured)
        
        co2_avoided = total_energy * co2_per_kwh
        estimated_savings = total_energy * price_per_kwh
        
        data = {
            'total_stations': total_stations,
            'total_inverters': total_inverters,
            'online_inverters': online_inverters,
            'offline_inverters': offline_inverters,
            'total_capacity_kw': capacity_sum,
            'current_power_w': power_sum,
            'today_energy_kwh': today_energy,
            'month_energy_kwh': month_energy,
            'total_energy_kwh': total_energy,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
            'co2_avoided_kg': co2_avoided,
            'estimated_savings': estimated_savings,
        }
        
        serializer = SolarDashboardSerializer(data)
        return Response(serializer.data)
