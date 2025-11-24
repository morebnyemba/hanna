'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Activity,
  Zap,
  Wifi,
  Battery,
  Server,
  AlertCircle,
  CheckCircle,
  XCircle,
  Search,
  TrendingUp,
  TrendingDown,
  Users
} from 'lucide-react';

interface Device {
  id: string;
  name: string;
  type: 'inverter' | 'starlink' | 'solar_panel' | 'battery';
  customer_name: string;
  customer_id: string;
  status: 'online' | 'offline' | 'warning' | 'critical';
  last_seen: string;
  metrics: {
    battery_level?: number;
    power_output?: number;
    temperature?: number;
    signal_strength?: number;
    uptime?: number;
  };
  location: string;
}

// Dummy data for demonstration
const generateDummyDevices = (): Device[] => {
  const customers = [
    { id: 'C001', name: 'John Doe' },
    { id: 'C002', name: 'Jane Smith' },
    { id: 'C003', name: 'Bob Johnson' },
    { id: 'C004', name: 'Alice Williams' },
    { id: 'C005', name: 'Charlie Brown' },
    { id: 'C006', name: 'Diana Prince' },
    { id: 'C007', name: 'Eve Adams' },
    { id: 'C008', name: 'Frank Miller' },
  ];

  const statuses: Array<'online' | 'offline' | 'warning' | 'critical'> = ['online', 'online', 'online', 'offline', 'warning', 'critical'];
  const deviceTypes: Array<'inverter' | 'starlink' | 'solar_panel' | 'battery'> = ['inverter', 'starlink', 'solar_panel', 'battery'];
  const locations = ['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Kwekwe', 'Masvingo'];

  return customers.flatMap((customer, idx) => {
    const numDevices = Math.floor(Math.random() * 3) + 1;
    return Array.from({ length: numDevices }, (_, i) => {
      const type = deviceTypes[Math.floor(Math.random() * deviceTypes.length)];
      const status = statuses[Math.floor(Math.random() * statuses.length)];
      
      return {
        id: `DEV-${customer.id}-${i + 1}`,
        name: `${type.charAt(0).toUpperCase() + type.slice(1)} ${i + 1}`,
        type,
        customer_name: customer.name,
        customer_id: customer.id,
        status,
        last_seen: new Date(Date.now() - Math.random() * 3600000).toISOString(),
        metrics: {
          battery_level: type === 'battery' || type === 'inverter' ? Math.floor(Math.random() * 100) : undefined,
          power_output: type === 'inverter' || type === 'solar_panel' ? Math.floor(Math.random() * 5000) : undefined,
          temperature: Math.floor(Math.random() * 40) + 20,
          signal_strength: type === 'starlink' ? Math.floor(Math.random() * 100) : undefined,
          uptime: Math.floor(Math.random() * 30),
        },
        location: locations[Math.floor(Math.random() * locations.length)],
      };
    });
  });
};

export default function AdminDeviceMonitoringPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterType, setFilterType] = useState<string>('all');

  useEffect(() => {
    // Simulate API call
    setTimeout(() => {
      setDevices(generateDummyDevices());
      setLoading(false);
    }, 1000);

    // Simulate real-time updates
    const interval = setInterval(() => {
      setDevices(prev => prev.map(device => ({
        ...device,
        status: Math.random() > 0.95 ? 
          (['online', 'offline', 'warning', 'critical'] as const)[Math.floor(Math.random() * 4)] : 
          device.status,
        metrics: {
          ...device.metrics,
          battery_level: device.metrics.battery_level ? Math.max(0, Math.min(100, device.metrics.battery_level + (Math.random() - 0.5) * 5)) : undefined,
          power_output: device.metrics.power_output ? Math.max(0, device.metrics.power_output + (Math.random() - 0.5) * 200) : undefined,
        }
      })));
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'offline': return <XCircle className="w-4 h-4 text-gray-400" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      case 'critical': return <AlertCircle className="w-4 h-4 text-red-600" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'offline': return 'bg-gray-100 text-gray-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDeviceIcon = (type: string) => {
    switch (type) {
      case 'inverter': return <Zap className="w-5 h-5 text-blue-600" />;
      case 'starlink': return <Wifi className="w-5 h-5 text-purple-600" />;
      case 'solar_panel': return <Activity className="w-5 h-5 text-yellow-600" />;
      case 'battery': return <Battery className="w-5 h-5 text-green-600" />;
      default: return <Server className="w-5 h-5" />;
    }
  };

  const stats = {
    total: devices.length,
    online: devices.filter(d => d.status === 'online').length,
    offline: devices.filter(d => d.status === 'offline').length,
    warning: devices.filter(d => d.status === 'warning').length,
    critical: devices.filter(d => d.status === 'critical').length,
    customers: new Set(devices.map(d => d.customer_id)).size,
  };

  const filteredDevices = devices.filter(device => {
    const matchesSearch = 
      device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.customer_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      device.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || device.status === filterStatus;
    const matchesType = filterType === 'all' || device.type === filterType;
    return matchesSearch && matchesStatus && matchesType;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading device monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="w-8 h-8 text-blue-600" />
          Device Monitoring Dashboard
        </h1>
        <p className="text-gray-600 mt-1">Real-time monitoring of all customer devices</p>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Devices</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Customers</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.customers}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Online</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.online}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Offline</CardTitle>
            <XCircle className="h-4 w-4 text-gray-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-gray-600">{stats.offline}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Warnings</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">{stats.warning}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Critical</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.critical}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search devices, customers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>

            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Statuses</option>
              <option value="online">Online</option>
              <option value="offline">Offline</option>
              <option value="warning">Warning</option>
              <option value="critical">Critical</option>
            </select>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Device Types</option>
              <option value="inverter">Inverters</option>
              <option value="starlink">Starlink Routers</option>
              <option value="solar_panel">Solar Panels</option>
              <option value="battery">Batteries</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Devices Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDevices.map((device) => (
          <Card key={device.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {getDeviceIcon(device.type)}
                  <div>
                    <CardTitle className="text-lg">{device.name}</CardTitle>
                    <p className="text-sm text-gray-500">{device.id}</p>
                  </div>
                </div>
                <Badge className={getStatusColor(device.status)}>
                  <div className="flex items-center gap-1">
                    {getStatusIcon(device.status)}
                    {device.status}
                  </div>
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Customer Info */}
              <div className="border-t pt-3">
                <p className="text-sm text-gray-500">Customer</p>
                <p className="font-medium">{device.customer_name}</p>
                <p className="text-xs text-gray-400">{device.location}</p>
              </div>

              {/* Metrics */}
              <div className="space-y-2">
                {device.metrics.battery_level !== undefined && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Battery Level</span>
                    <span className="font-semibold flex items-center gap-1">
                      {device.metrics.battery_level.toFixed(0)}%
                      {device.metrics.battery_level > 50 ? (
                        <TrendingUp className="w-3 h-3 text-green-600" />
                      ) : (
                        <TrendingDown className="w-3 h-3 text-red-600" />
                      )}
                    </span>
                  </div>
                )}

                {device.metrics.power_output !== undefined && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Power Output</span>
                    <span className="font-semibold">{device.metrics.power_output.toFixed(0)}W</span>
                  </div>
                )}

                {device.metrics.signal_strength !== undefined && (
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Signal Strength</span>
                    <span className="font-semibold">{device.metrics.signal_strength.toFixed(0)}%</span>
                  </div>
                )}

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Temperature</span>
                  <span className="font-semibold">{device.metrics.temperature}°C</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Uptime</span>
                  <span className="font-semibold">{device.metrics.uptime} days</span>
                </div>
              </div>

              {/* Last Seen */}
              <div className="border-t pt-3 text-xs text-gray-500">
                Last seen: {new Date(device.last_seen).toLocaleString()}
              </div>

              <Button variant="outline" className="w-full" size="sm">
                View Details
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredDevices.length === 0 && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center text-gray-500">
              <Server className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-xl font-semibold mb-2">No Devices Found</h3>
              <p>No devices match your current filters</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
