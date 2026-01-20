"""
Solar Integration Services

This module provides service classes for interacting with various solar inverter
monitoring APIs. The primary focus is on Deye inverters, with an extensible
architecture for adding other brands.
"""

import hashlib
import hmac
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import requests
from django.db import transaction
from django.utils import timezone

from .models import (
    DailyEnergyStats,
    InverterDataPoint,
    SolarAlert,
    SolarAPICredential,
    SolarInverter,
    SolarInverterBrand,
    SolarStation,
)

logger = logging.getLogger(__name__)


class BaseSolarAPIService(ABC):
    """
    Abstract base class for solar inverter API services.
    Provides common functionality and defines the interface for brand-specific implementations.
    """
    
    def __init__(self, credential: SolarAPICredential):
        self.credential = credential
        self.brand = credential.brand
        self.base_url = credential.brand.api_base_url or ""
        self.session = requests.Session()
        self.session.timeout = 30
    
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the API and obtain/refresh tokens."""
        pass
    
    @abstractmethod
    def get_stations(self) -> List[Dict[str, Any]]:
        """Retrieve list of solar stations/plants."""
        pass
    
    @abstractmethod
    def get_station_details(self, station_external_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific station."""
        pass
    
    @abstractmethod
    def get_inverters(self, station_external_id: str) -> List[Dict[str, Any]]:
        """Get list of inverters for a station."""
        pass
    
    @abstractmethod
    def get_inverter_realtime_data(self, inverter_external_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time data from an inverter."""
        pass
    
    @abstractmethod
    def get_inverter_history(
        self, 
        inverter_external_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical data for an inverter."""
        pass
    
    def sync_all(self) -> Tuple[bool, str]:
        """
        Full synchronization of all data from the API.
        Returns (success, message).
        """
        try:
            self.credential.sync_status = 'syncing'
            self.credential.save(update_fields=['sync_status'])
            
            # Authenticate first
            if not self.authenticate():
                raise Exception("Authentication failed")
            
            # Sync stations
            stations_data = self.get_stations()
            for station_data in stations_data:
                self._sync_station(station_data)
            
            self.credential.sync_status = 'success'
            self.credential.last_sync_at = timezone.now()
            self.credential.sync_error = ''
            self.credential.save(update_fields=['sync_status', 'last_sync_at', 'sync_error'])
            
            return True, f"Successfully synced {len(stations_data)} stations"
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sync failed for credential {self.credential.id}: {error_msg}", exc_info=True)
            self.credential.sync_status = 'error'
            self.credential.sync_error = error_msg[:500]
            self.credential.save(update_fields=['sync_status', 'sync_error'])
            return False, error_msg
    
    def _sync_station(self, station_data: Dict[str, Any]) -> SolarStation:
        """Sync a single station and its inverters."""
        external_id = station_data.get('id') or station_data.get('station_id') or station_data.get('plant_id')
        
        station, created = SolarStation.objects.update_or_create(
            credential=self.credential,
            external_id=str(external_id),
            defaults={
                'name': station_data.get('name', f'Station {external_id}'),
                'address': station_data.get('address', ''),
                'latitude': station_data.get('latitude'),
                'longitude': station_data.get('longitude'),
                'total_capacity_kw': station_data.get('capacity_kw'),
                'status': self._map_station_status(station_data.get('status')),
                'metadata': station_data,
                'last_data_time': timezone.now(),
            }
        )
        
        # Sync inverters for this station
        inverters_data = self.get_inverters(str(external_id))
        for inverter_data in inverters_data:
            self._sync_inverter(station, inverter_data)
        
        return station
    
    def _sync_inverter(self, station: SolarStation, inverter_data: Dict[str, Any]) -> SolarInverter:
        """Sync a single inverter."""
        external_id = inverter_data.get('id') or inverter_data.get('device_id') or inverter_data.get('sn')
        
        inverter, created = SolarInverter.objects.update_or_create(
            station=station,
            external_id=str(external_id),
            defaults={
                'serial_number': inverter_data.get('sn', inverter_data.get('serial_number', '')),
                'model': inverter_data.get('model', inverter_data.get('device_type', '')),
                'rated_power_kw': inverter_data.get('rated_power'),
                'firmware_version': inverter_data.get('firmware', ''),
                'status': self._map_inverter_status(inverter_data.get('status')),
                'metadata': inverter_data,
            }
        )
        
        # Get and save real-time data
        realtime_data = self.get_inverter_realtime_data(str(external_id))
        if realtime_data:
            self.update_inverter_realtime(inverter, realtime_data)
        
        return inverter
    
    def update_inverter_realtime(self, inverter: SolarInverter, data: Dict[str, Any]):
        """Update inverter with real-time data."""
        inverter.current_power_w = data.get('power_w') or data.get('pac')
        inverter.today_energy_kwh = data.get('today_energy_kwh') or data.get('e_today')
        inverter.total_energy_kwh = data.get('total_energy_kwh') or data.get('e_total')
        inverter.grid_voltage_v = data.get('grid_voltage') or data.get('vac')
        inverter.grid_frequency_hz = data.get('grid_frequency') or data.get('fac')
        inverter.pv1_voltage_v = data.get('pv1_voltage') or data.get('vpv1')
        inverter.pv1_current_a = data.get('pv1_current') or data.get('ipv1')
        inverter.pv1_power_w = data.get('pv1_power') or data.get('ppv1')
        inverter.pv2_voltage_v = data.get('pv2_voltage') or data.get('vpv2')
        inverter.pv2_current_a = data.get('pv2_current') or data.get('ipv2')
        inverter.pv2_power_w = data.get('pv2_power') or data.get('ppv2')
        inverter.battery_voltage_v = data.get('battery_voltage') or data.get('vbat')
        inverter.battery_current_a = data.get('battery_current') or data.get('ibat')
        inverter.battery_power_w = data.get('battery_power') or data.get('pbat')
        inverter.battery_soc_percent = data.get('battery_soc') or data.get('soc')
        inverter.battery_temperature_c = data.get('battery_temperature') or data.get('tbat')
        inverter.load_power_w = data.get('load_power') or data.get('pload')
        inverter.grid_power_w = data.get('grid_power') or data.get('pgrid')
        inverter.inverter_temperature_c = data.get('temperature') or data.get('temp')
        inverter.last_data_time = timezone.now()
        inverter.status = self._map_inverter_status(data.get('status', 'online'))
        inverter.save()
        
        # Also create a data point for historical tracking
        InverterDataPoint.objects.update_or_create(
            inverter=inverter,
            timestamp=timezone.now().replace(second=0, microsecond=0),  # Round to minute
            defaults={
                'power_w': inverter.current_power_w,
                'pv_power_w': (inverter.pv1_power_w or 0) + (inverter.pv2_power_w or 0),
                'load_power_w': inverter.load_power_w,
                'grid_power_w': inverter.grid_power_w,
                'battery_power_w': inverter.battery_power_w,
                'battery_soc': inverter.battery_soc_percent,
                'grid_voltage_v': inverter.grid_voltage_v,
                'grid_frequency_hz': inverter.grid_frequency_hz,
                'temperature_c': inverter.inverter_temperature_c,
                'status': inverter.status,
                'raw_data': data,
            }
        )
    
    def _map_station_status(self, api_status: Optional[str]) -> str:
        """Map API status to our status choices."""
        if not api_status:
            return 'unknown'
        status_lower = str(api_status).lower()
        if status_lower in ['online', 'normal', 'running', '1']:
            return 'online'
        elif status_lower in ['offline', 'disconnected', '0']:
            return 'offline'
        elif status_lower in ['warning', 'alarm']:
            return 'warning'
        elif status_lower in ['fault', 'error', 'failure']:
            return 'fault'
        return 'unknown'
    
    def _map_inverter_status(self, api_status: Optional[str]) -> str:
        """Map API inverter status to our status choices."""
        if not api_status:
            return 'unknown'
        status_lower = str(api_status).lower()
        if status_lower in ['online', 'normal', 'running', 'generating', '1']:
            return 'online'
        elif status_lower in ['offline', 'disconnected', '0']:
            return 'offline'
        elif status_lower in ['standby', 'idle', 'waiting']:
            return 'standby'
        elif status_lower in ['warning', 'alarm']:
            return 'warning'
        elif status_lower in ['fault', 'error', 'failure']:
            return 'fault'
        return 'unknown'


class DeyeCloudAPIService(BaseSolarAPIService):
    """
    Service for interacting with Deye Cloud API.
    
    Deye Cloud API provides monitoring data for Deye solar inverters.
    The API uses a token-based authentication with HMAC signature.
    """
    
    # Deye Cloud API endpoints
    API_BASE_URL = "https://openapi.solarkcloud.com"
    
    def __init__(self, credential: SolarAPICredential):
        super().__init__(credential)
        self.base_url = self.API_BASE_URL
        self.app_id = credential.api_key
        self.app_secret = credential.api_secret
        self.access_token = credential.access_token
        self.email = credential.account_id  # Deye uses email for login
    
    def _generate_signature(self, timestamp: str, nonce: str) -> str:
        """Generate HMAC-SHA256 signature for API requests."""
        sign_str = f"{self.app_id}{timestamp}{nonce}"
        signature = hmac.new(
            self.app_secret.encode('utf-8'),
            sign_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers for API requests including signature."""
        timestamp = str(int(time.time() * 1000))
        nonce = hashlib.md5(timestamp.encode()).hexdigest()[:16]
        signature = self._generate_signature(timestamp, nonce)
        
        return {
            "Content-Type": "application/json",
            "appId": self.app_id,
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": signature,
            "Authorization": f"Bearer {self.access_token}" if self.access_token else "",
        }
    
    def authenticate(self) -> bool:
        """
        Authenticate with Deye Cloud API.
        Uses email/password or refreshes existing token.
        """
        try:
            # Check if we have a valid token
            if self.access_token and not self.credential.is_token_expired():
                logger.info(f"Using existing valid token for credential {self.credential.id}")
                return True
            
            # Need to get new token
            url = f"{self.base_url}/v1/oauth/token"
            
            headers = self._get_headers()
            headers.pop("Authorization", None)  # Remove auth for token request
            
            payload = {
                "appId": self.app_id,
                "email": self.email,
                "password": self.credential.api_secret,  # Using secret as password
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') or data.get('code') == 0:
                token_data = data.get('data', data)
                self.access_token = token_data.get('accessToken') or token_data.get('access_token')
                
                # Update credential with new token
                self.credential.access_token = self.access_token
                expires_in = token_data.get('expiresIn', 7200)  # Default 2 hours
                self.credential.token_expires_at = timezone.now() + timedelta(seconds=expires_in)
                self.credential.save(update_fields=['access_token', 'token_expires_at'])
                
                logger.info(f"Successfully authenticated with Deye Cloud for credential {self.credential.id}")
                return True
            else:
                error_msg = data.get('msg') or data.get('message') or 'Unknown error'
                logger.error(f"Deye authentication failed: {error_msg}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Deye authentication request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Deye authentication error: {e}", exc_info=True)
            return False
    
    def get_stations(self) -> List[Dict[str, Any]]:
        """Get list of power stations/plants."""
        try:
            if not self.authenticate():
                return []
            
            url = f"{self.base_url}/v1/plant/list"
            headers = self._get_headers()
            
            # Deye uses pagination
            all_stations = []
            page = 1
            page_size = 100
            
            while True:
                payload = {
                    "page": page,
                    "size": page_size,
                }
                
                response = self.session.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success') or data.get('code') == 0:
                    stations = data.get('data', {}).get('list', [])
                    all_stations.extend(stations)
                    
                    total = data.get('data', {}).get('total', 0)
                    if len(all_stations) >= total or not stations:
                        break
                    page += 1
                else:
                    logger.warning(f"Failed to get Deye stations: {data.get('msg')}")
                    break
            
            logger.info(f"Retrieved {len(all_stations)} stations from Deye Cloud")
            return all_stations
            
        except Exception as e:
            logger.error(f"Error getting Deye stations: {e}", exc_info=True)
            return []
    
    def get_station_details(self, station_external_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific station."""
        try:
            if not self.authenticate():
                return None
            
            url = f"{self.base_url}/v1/plant/detail"
            headers = self._get_headers()
            
            payload = {
                "stationId": station_external_id,
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') or data.get('code') == 0:
                return data.get('data', {})
            else:
                logger.warning(f"Failed to get Deye station details: {data.get('msg')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Deye station details: {e}", exc_info=True)
            return None
    
    def get_inverters(self, station_external_id: str) -> List[Dict[str, Any]]:
        """Get list of inverters for a station."""
        try:
            if not self.authenticate():
                return []
            
            url = f"{self.base_url}/v1/device/list"
            headers = self._get_headers()
            
            all_inverters = []
            page = 1
            page_size = 100
            
            while True:
                payload = {
                    "stationId": station_external_id,
                    "page": page,
                    "size": page_size,
                }
                
                response = self.session.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('success') or data.get('code') == 0:
                    inverters = data.get('data', {}).get('list', [])
                    all_inverters.extend(inverters)
                    
                    total = data.get('data', {}).get('total', 0)
                    if len(all_inverters) >= total or not inverters:
                        break
                    page += 1
                else:
                    logger.warning(f"Failed to get Deye inverters: {data.get('msg')}")
                    break
            
            logger.info(f"Retrieved {len(all_inverters)} inverters from Deye Cloud for station {station_external_id}")
            return all_inverters
            
        except Exception as e:
            logger.error(f"Error getting Deye inverters: {e}", exc_info=True)
            return []
    
    def get_inverter_realtime_data(self, inverter_external_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time data from an inverter."""
        try:
            if not self.authenticate():
                return None
            
            url = f"{self.base_url}/v1/device/realtime"
            headers = self._get_headers()
            
            payload = {
                "sn": inverter_external_id,
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') or data.get('code') == 0:
                raw_data = data.get('data', {})
                
                # Transform Deye data to our standard format
                return {
                    'power_w': raw_data.get('pac'),
                    'today_energy_kwh': raw_data.get('eToday'),
                    'total_energy_kwh': raw_data.get('eTotal'),
                    'grid_voltage': raw_data.get('vac1'),
                    'grid_frequency': raw_data.get('fac'),
                    'pv1_voltage': raw_data.get('vpv1'),
                    'pv1_current': raw_data.get('ipv1'),
                    'pv1_power': raw_data.get('ppv1'),
                    'pv2_voltage': raw_data.get('vpv2'),
                    'pv2_current': raw_data.get('ipv2'),
                    'pv2_power': raw_data.get('ppv2'),
                    'battery_voltage': raw_data.get('vbat'),
                    'battery_current': raw_data.get('ibat'),
                    'battery_power': raw_data.get('pbat'),
                    'battery_soc': raw_data.get('soc'),
                    'battery_temperature': raw_data.get('tbat'),
                    'load_power': raw_data.get('pload'),
                    'grid_power': raw_data.get('pgrid'),
                    'temperature': raw_data.get('temp'),
                    'status': raw_data.get('status'),
                    'raw': raw_data,
                }
            else:
                logger.warning(f"Failed to get Deye realtime data: {data.get('msg')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Deye realtime data: {e}", exc_info=True)
            return None
    
    def get_inverter_history(
        self, 
        inverter_external_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get historical data for an inverter."""
        try:
            if not self.authenticate():
                return []
            
            url = f"{self.base_url}/v1/device/history"
            headers = self._get_headers()
            
            payload = {
                "sn": inverter_external_id,
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
            }
            
            response = self.session.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') or data.get('code') == 0:
                return data.get('data', {}).get('list', [])
            else:
                logger.warning(f"Failed to get Deye history data: {data.get('msg')}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting Deye history data: {e}", exc_info=True)
            return []


class SolarServiceFactory:
    """Factory for creating the appropriate solar API service based on brand."""
    
    _services = {
        'deye': DeyeCloudAPIService,
        # Add more brands here as they are implemented
        # 'growatt': GrowattCloudAPIService,
        # 'goodwe': GoodWeAPIService,
        # 'sungrow': SungrowAPIService,
    }
    
    @classmethod
    def get_service(cls, credential: SolarAPICredential) -> Optional[BaseSolarAPIService]:
        """
        Get the appropriate service class for a credential's brand.
        
        Args:
            credential: The API credential to use
            
        Returns:
            An instance of the appropriate service class, or None if brand not supported
        """
        brand_code = credential.brand.code.lower()
        service_class = cls._services.get(brand_code)
        
        if service_class:
            return service_class(credential)
        else:
            logger.warning(f"No service implementation for brand: {credential.brand.name}")
            return None
    
    @classmethod
    def register_service(cls, brand_code: str, service_class: type):
        """Register a new service class for a brand."""
        cls._services[brand_code.lower()] = service_class


def sync_all_solar_credentials():
    """
    Sync all active solar API credentials.
    Called by Celery beat or manually.
    """
    credentials = SolarAPICredential.objects.filter(is_active=True).select_related('brand')
    results = []
    
    for credential in credentials:
        service = SolarServiceFactory.get_service(credential)
        if service:
            success, message = service.sync_all()
            results.append({
                'credential_id': str(credential.id),
                'credential_name': credential.name,
                'brand': credential.brand.name,
                'success': success,
                'message': message,
            })
        else:
            results.append({
                'credential_id': str(credential.id),
                'credential_name': credential.name,
                'brand': credential.brand.name,
                'success': False,
                'message': 'No service implementation available',
            })
    
    return results


def check_and_create_alerts():
    """
    Check all inverters for alert conditions and create alerts as needed.
    """
    # Check for offline inverters
    offline_threshold = timezone.now() - timedelta(minutes=30)
    offline_inverters = SolarInverter.objects.filter(
        is_active=True,
        last_data_time__lt=offline_threshold,
        status__in=['online', 'standby']
    )
    
    for inverter in offline_inverters:
        # Check if there's already an active offline alert
        existing_alert = SolarAlert.objects.filter(
            inverter=inverter,
            alert_type=SolarAlert.AlertType.OFFLINE,
            is_active=True
        ).first()
        
        if not existing_alert:
            SolarAlert.objects.create(
                station=inverter.station,
                inverter=inverter,
                alert_type=SolarAlert.AlertType.OFFLINE,
                severity=SolarAlert.Severity.WARNING,
                title=f"Inverter Offline: {inverter.serial_number or inverter.external_id}",
                description=f"Inverter has not reported data since {inverter.last_data_time}",
            )
            logger.info(f"Created offline alert for inverter {inverter.id}")
    
    # Check for low battery
    low_battery_inverters = SolarInverter.objects.filter(
        is_active=True,
        battery_soc_percent__lt=20,
        battery_soc_percent__isnull=False
    )
    
    for inverter in low_battery_inverters:
        existing_alert = SolarAlert.objects.filter(
            inverter=inverter,
            alert_type=SolarAlert.AlertType.BATTERY_LOW,
            is_active=True
        ).first()
        
        if not existing_alert:
            SolarAlert.objects.create(
                station=inverter.station,
                inverter=inverter,
                alert_type=SolarAlert.AlertType.BATTERY_LOW,
                severity=SolarAlert.Severity.WARNING,
                title=f"Low Battery: {inverter.serial_number or inverter.external_id}",
                description=f"Battery state of charge is {inverter.battery_soc_percent}%",
            )
            logger.info(f"Created low battery alert for inverter {inverter.id}")
    
    # Check for fault status
    fault_inverters = SolarInverter.objects.filter(
        is_active=True,
        status='fault'
    )
    
    for inverter in fault_inverters:
        existing_alert = SolarAlert.objects.filter(
            inverter=inverter,
            alert_type=SolarAlert.AlertType.FAULT,
            is_active=True
        ).first()
        
        if not existing_alert:
            SolarAlert.objects.create(
                station=inverter.station,
                inverter=inverter,
                alert_type=SolarAlert.AlertType.FAULT,
                severity=SolarAlert.Severity.ERROR,
                title=f"Inverter Fault: {inverter.serial_number or inverter.external_id}",
                description="Inverter is reporting a fault condition. Check error codes.",
                code=inverter.metadata.get('error_code', ''),
            )
            logger.info(f"Created fault alert for inverter {inverter.id}")
