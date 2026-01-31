'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useAuthStore } from '@/app/store/authStore';
import { 
  Activity,
  Zap,
  Wifi,
  Battery,
  AlertCircle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Settings,
  RefreshCw
} from 'lucide-react';

interface Installation {
  id: string;
  installation_type: string;
  system_size: number;
  capacity_unit: string;
  installation_address: string;
  installation_status: string;
  installation_date: string;
}

export default function ClientDashboardPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const { accessToken } = useAuthStore();

  const fetchInstallations = async (showLoading = true) => {
    if (showLoading) setRefreshing(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/client/installations/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch installations (${response.status})`);
      }

      const data = await response.json();
      setInstallations(data.results || data || []);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load installations');
      console.error('Installation fetch error:', err);
    } finally {
      if (showLoading) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchInstallations();
    }
  }, [accessToken]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your installations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-600" />
            Dashboard
          </h1>
          <p className="text-gray-600 mt-1">Overview of your installations</p>
        </div>
        <Button 
          onClick={() => fetchInstallations(true)}
          disabled={refreshing}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-red-900 text-sm">Error Loading Data</h3>
              <p className="text-red-700 text-sm mt-1">{error}</p>
              <button
                onClick={() => fetchInstallations(true)}
                className="mt-2 inline-flex items-center gap-2 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
              >
                <RefreshCw className="h-4 w-4" /> Try Again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Installations</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{installations.length}</div>
            <p className="text-xs text-muted-foreground">
              {installations.filter(i => i.installation_status === 'active').length} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Installation Types</CardTitle>
            <Zap className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {new Set(installations.map(i => i.installation_type)).size}
            </div>
            <p className="text-xs text-muted-foreground">Different system types</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Capacity</CardTitle>
            <Battery className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {installations.reduce((sum, i) => sum + (i.system_size || 0), 0).toFixed(1)}
            </div>
            <p className="text-xs text-muted-foreground">
              {installations[0]?.capacity_unit || 'kW'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Installations List */}
      <Card>
        <CardHeader>
          <CardTitle>Your Installations</CardTitle>
        </CardHeader>
        <CardContent>
          {installations.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">No installations found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {installations.map((installation) => (
                <div key={installation.id} className="border rounded-lg p-4 hover:bg-gray-50 transition">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">
                        {installation.installation_type}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {installation.installation_address}
                      </p>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-xs text-gray-500">
                          System: {installation.system_size} {installation.capacity_unit}
                        </span>
                        <span className="text-xs text-gray-500">
                          Installed: {new Date(installation.installation_date).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Badge className={
                      installation.installation_status === 'active' 
                        ? 'bg-green-100 text-green-800'
                        : installation.installation_status === 'commissioned'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }>
                      {installation.installation_status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
          <div>
            <h3 className="font-semibold text-blue-900 text-sm">Preview Mode - Demo Data</h3>
            <p className="text-blue-700 text-sm mt-1">
              This dashboard shows sample device data. Real-time monitoring will be available once your installation includes remote monitoring hardware.
            </p>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{devices.length}</div>
            <p className="text-xs text-muted-foreground">
              {devices.filter(d => d.status === 'online').length} online
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Power Output</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalPowerOutput.toFixed(0)}W</div>
            <p className="text-xs text-muted-foreground">
              Consuming {totalPowerConsumption.toFixed(0)}W
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Avg Battery</CardTitle>
            <Battery className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{avgBatteryLevel.toFixed(0)}%</div>
            <p className="text-xs text-muted-foreground">
              Across {inverters.length} inverters
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connectivity</CardTitle>
            <Wifi className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{starlinks.filter(s => s.status === 'online').length}/{starlinks.length}</div>
            <p className="text-xs text-muted-foreground">Starlink routers online</p>
          </CardContent>
        </Card>
      </div>

      {/* Inverters Section */}
      <div>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Zap className="w-6 h-6 text-blue-600" />
          Inverters
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {inverters.map((device) => (
            <Card key={device.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getDeviceIcon(device.type)}
                    <div>
                      <CardTitle className="text-xl">{device.name}</CardTitle>
                      <p className="text-sm text-gray-500">{device.serial_number}</p>
                    </div>
                  </div>
                  <Badge className={`${getStatusColor(device.status)} border`}>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(device.status)}
                      {device.status}
                    </div>
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Battery Level */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Battery Level</span>
                    <span className="font-semibold flex items-center gap-1">
                      {device.metrics.battery_level?.toFixed(0)}%
                      {(device.metrics.battery_level || 0) > 50 ? (
                        <TrendingUp className="w-3 h-3 text-green-600" />
                      ) : (
                        <TrendingDown className="w-3 h-3 text-red-600" />
                      )}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        (device.metrics.battery_level || 0) > 60 ? 'bg-green-500' :
                        (device.metrics.battery_level || 0) > 30 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${device.metrics.battery_level}%` }}
                    ></div>
                  </div>
                </div>

                {/* Power Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Power Output</p>
                    <p className="text-lg font-bold text-green-600">{device.metrics.power_output}W</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Consumption</p>
                    <p className="text-lg font-bold text-orange-600">{device.metrics.power_consumption}W</p>
                  </div>
                </div>

                {/* Temperature & Uptime */}
                <div className="grid grid-cols-2 gap-4 pt-2 border-t">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Temperature</span>
                    <span className={`font-semibold ${
                      (device.metrics.temperature || 0) > 45 ? 'text-red-600' : 'text-gray-900'
                    }`}>
                      {device.metrics.temperature}°C
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Uptime</span>
                    <span className="font-semibold">{device.metrics.uptime_hours}h</span>
                  </div>
                </div>

                {/* Footer Info */}
                <div className="border-t pt-3 space-y-1">
                  <p className="text-xs text-gray-500">
                    Installed: {new Date(device.installed_date).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    Last seen: {new Date(device.last_seen).toLocaleString()}
                  </p>
                </div>

                <Button variant="outline" className="w-full" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Device Settings
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Starlink Routers Section */}
      <div>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Wifi className="w-6 h-6 text-purple-600" />
          Starlink Routers
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {starlinks.map((device) => (
            <Card key={device.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    {getDeviceIcon(device.type)}
                    <div>
                      <CardTitle className="text-xl">{device.name}</CardTitle>
                      <p className="text-sm text-gray-500">{device.serial_number}</p>
                    </div>
                  </div>
                  <Badge className={`${getStatusColor(device.status)} border`}>
                    <div className="flex items-center gap-1">
                      {getStatusIcon(device.status)}
                      {device.status}
                    </div>
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Signal Strength */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-gray-600">Signal Strength</span>
                    <span className="font-semibold">{device.metrics.signal_strength?.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        (device.metrics.signal_strength || 0) > 70 ? 'bg-green-500' :
                        (device.metrics.signal_strength || 0) > 40 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${device.metrics.signal_strength}%` }}
                    ></div>
                  </div>
                </div>

                {/* Data Usage & Temperature */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-gray-500">Data Usage</p>
                    <p className="text-lg font-bold text-blue-600">{device.metrics.data_usage_gb?.toFixed(1)} GB</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Temperature</p>
                    <p className={`text-lg font-bold ${
                      (device.metrics.temperature || 0) > 50 ? 'text-red-600' : 'text-gray-900'
                    }`}>
                      {device.metrics.temperature}°C
                    </p>
                  </div>
                </div>

                {/* Uptime */}
                <div className="border-t pt-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Uptime</span>
                    <span className="font-semibold">{device.metrics.uptime_hours}h</span>
                  </div>
                </div>

                {/* Footer Info */}
                <div className="border-t pt-3 space-y-1">
                  <p className="text-xs text-gray-500">
                    Installed: {new Date(device.installed_date).toLocaleDateString()}
                  </p>
                  <p className="text-xs text-gray-500">
                    Last seen: {new Date(device.last_seen).toLocaleString()}
                  </p>
                </div>

                <Button variant="outline" className="w-full" size="sm">
                  <Settings className="w-4 h-4 mr-2" />
                  Router Settings
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Alert Section */}
      {devices.some(d => d.status === 'warning' || d.status === 'critical') && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertCircle className="w-5 h-5" />
              Devices Requiring Attention
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2">
              {devices
                .filter(d => d.status === 'warning' || d.status === 'critical')
                .map(device => (
                  <li key={device.id} className="flex items-center justify-between">
                    <span className="text-sm">{device.name} - {device.type}</span>
                    <Badge className={getStatusColor(device.status)}>
                      {device.status}
                    </Badge>
                  </li>
                ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}