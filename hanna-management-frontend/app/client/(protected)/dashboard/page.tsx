'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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

interface Device {
  id: string;
  name: string;
  type: 'inverter' | 'starlink';
  status: 'online' | 'offline' | 'warning' | 'critical';
  last_seen: string;
  metrics: {
    battery_level?: number;
    power_output?: number;
    power_consumption?: number;
    temperature?: number;
    signal_strength?: number;
    uptime_hours?: number;
    data_usage_gb?: number;
  };
  installed_date: string;
  serial_number: string;
}

// Dummy data for client's devices
const generateClientDevices = (): Device[] => {
  return [
    {
      id: 'INV-001',
      name: 'Main Inverter',
      type: 'inverter',
      status: 'online',
      last_seen: new Date(Date.now() - 120000).toISOString(),
      metrics: {
        battery_level: 85,
        power_output: 3500,
        power_consumption: 2800,
        temperature: 38,
        uptime_hours: 720,
      },
      installed_date: '2024-01-15',
      serial_number: 'INV-2024-001-A7X',
    },
    {
      id: 'INV-002',
      name: 'Backup Inverter',
      type: 'inverter',
      status: 'online',
      last_seen: new Date(Date.now() - 300000).toISOString(),
      metrics: {
        battery_level: 92,
        power_output: 1200,
        power_consumption: 800,
        temperature: 35,
        uptime_hours: 680,
      },
      installed_date: '2024-02-10',
      serial_number: 'INV-2024-002-B5K',
    },
    {
      id: 'STL-001',
      name: 'Starlink Router',
      type: 'starlink',
      status: 'online',
      last_seen: new Date(Date.now() - 60000).toISOString(),
      metrics: {
        signal_strength: 78,
        temperature: 42,
        uptime_hours: 1440,
        data_usage_gb: 245.7,
      },
      installed_date: '2023-11-20',
      serial_number: 'STL-2023-001-C9M',
    },
    {
      id: 'STL-002',
      name: 'Starlink Backup',
      type: 'starlink',
      status: 'warning',
      last_seen: new Date(Date.now() - 1800000).toISOString(),
      metrics: {
        signal_strength: 45,
        temperature: 55,
        uptime_hours: 120,
        data_usage_gb: 89.3,
      },
      installed_date: '2024-03-05',
      serial_number: 'STL-2024-002-D2P',
    },
  ];
};

export default function ClientDashboardPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadDevices = () => {
    setRefreshing(true);
    setTimeout(() => {
      setDevices(generateClientDevices());
      setLoading(false);
      setRefreshing(false);
    }, 800);
  };

  useEffect(() => {
    loadDevices();

    // Simulate real-time updates every 10 seconds
    const interval = setInterval(() => {
      setDevices(prev => prev.map(device => ({
        ...device,
        last_seen: new Date().toISOString(),
        metrics: {
          ...device.metrics,
          battery_level: device.metrics.battery_level ? 
            Math.max(0, Math.min(100, device.metrics.battery_level + (Math.random() - 0.5) * 3)) : undefined,
          power_output: device.metrics.power_output ? 
            Math.max(0, device.metrics.power_output + (Math.random() - 0.5) * 100) : undefined,
          signal_strength: device.metrics.signal_strength ? 
            Math.max(0, Math.min(100, device.metrics.signal_strength + (Math.random() - 0.5) * 5)) : undefined,
          temperature: device.metrics.temperature ? 
            Math.max(20, Math.min(70, device.metrics.temperature + (Math.random() - 0.5) * 2)) : undefined,
        }
      })));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'offline': return <XCircle className="w-5 h-5 text-gray-400" />;
      case 'warning': return <AlertCircle className="w-5 h-5 text-yellow-600" />;
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-600" />;
      default: return <Activity className="w-5 h-5" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800 border-green-200';
      case 'offline': return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'inverter': return <Zap className="w-8 h-8 text-blue-600" />;
      case 'starlink': return <Wifi className="w-8 h-8 text-purple-600" />;
      default: return <Activity className="w-8 h-8" />;
    }
  };

  const inverters = devices.filter(d => d.type === 'inverter');
  const starlinks = devices.filter(d => d.type === 'starlink');

  const totalPowerOutput = inverters.reduce((sum, inv) => sum + (inv.metrics.power_output || 0), 0);
  const totalPowerConsumption = inverters.reduce((sum, inv) => sum + (inv.metrics.power_consumption || 0), 0);
  const avgBatteryLevel = inverters.length > 0 
    ? inverters.reduce((sum, inv) => sum + (inv.metrics.battery_level || 0), 0) / inverters.length 
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your devices...</p>
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
            My Devices
          </h1>
          <p className="text-gray-600 mt-1">Monitor your inverters and Starlink routers in real-time</p>
        </div>
        <Button 
          onClick={loadDevices} 
          disabled={refreshing}
          variant="outline"
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
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