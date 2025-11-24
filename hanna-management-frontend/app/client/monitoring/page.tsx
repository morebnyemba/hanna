"use client";
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Wifi, Battery, Zap, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface ClientDevice {
  id: string;
  name: string;
  type: 'inverter' | 'router' | 'battery';
  status: 'online' | 'offline' | 'warning';
  last_seen: string;
  metrics: {
    battery_level?: number;
    power_output?: number;
    signal_strength?: number;
  };
}

const generateClientDevices = (): ClientDevice[] => {
  const types: ClientDevice['type'][] = ['inverter', 'router', 'battery'];
  return Array.from({ length: 6 }).map((_, i) => {
    const type = types[Math.floor(Math.random() * types.length)];
    const statusPool: ClientDevice['status'][] = ['online', 'online', 'online', 'offline', 'warning'];
    const status = statusPool[Math.floor(Math.random() * statusPool.length)];
    return {
      id: `CLT-DEV-${i + 1}`,
      name: `${type === 'router' ? 'Starlink' : type.charAt(0).toUpperCase() + type.slice(1)} ${i + 1}`,
      type,
      status,
      last_seen: new Date(Date.now() - Math.random() * 1800000).toISOString(),
      metrics: {
        battery_level: type === 'battery' || type === 'inverter' ? Math.floor(Math.random() * 100) : undefined,
        power_output: type === 'inverter' ? Math.floor(Math.random() * 5000) : undefined,
        signal_strength: type === 'router' ? Math.floor(Math.random() * 100) : undefined,
      }
    };
  });
};

export default function ClientMonitoringPage() {
  const [devices, setDevices] = useState<ClientDevice[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setTimeout(() => {
      setDevices(generateClientDevices());
      setLoading(false);
    }, 600);
    const interval = setInterval(() => {
      setDevices(prev => prev.map(d => ({
        ...d,
        status: Math.random() > 0.97 ? (['online','offline','warning'] as const)[Math.floor(Math.random()*3)] : d.status,
        metrics: {
          ...d.metrics,
          battery_level: d.metrics.battery_level !== undefined ? Math.max(0, Math.min(100, d.metrics.battery_level + (Math.random()-0.5)*4)) : undefined,
          power_output: d.metrics.power_output !== undefined ? Math.max(0, d.metrics.power_output + (Math.random()-0.5)*150) : undefined,
          signal_strength: d.metrics.signal_strength !== undefined ? Math.max(0, Math.min(100, d.metrics.signal_strength + (Math.random()-0.5)*10)) : undefined,
        }
      })));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: ClientDevice['status']) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'offline': return <XCircle className="w-4 h-4 text-gray-400" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-600" />;
      default: return <Activity className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status: ClientDevice['status']) => {
    switch (status) {
      case 'online': return 'bg-green-100 text-green-800';
      case 'offline': return 'bg-gray-100 text-gray-800';
      case 'warning': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity className="w-8 h-8 text-purple-600" />
          Your Device Monitoring
        </h1>
        <p className="text-gray-600 mt-1">Status overview of your installed system components</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2"><Activity className="h-4 w-4" />Total Devices</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold">{devices.length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2"><CheckCircle className="h-4 w-4 text-green-600" />Online</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold text-green-600">{devices.filter(d=>d.status==='online').length}</div></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2"><AlertCircle className="h-4 w-4 text-red-600" />Attention</CardTitle>
          </CardHeader>
          <CardContent><div className="text-2xl font-bold text-red-600">{devices.filter(d=>d.status!=='online').length}</div></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {devices.map(device => (
          <Card key={device.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {device.type === 'inverter' && <Zap className="w-5 h-5 text-blue-600" />}
                  {device.type === 'router' && <Wifi className="w-5 h-5 text-purple-600" />}
                  {device.type === 'battery' && <Battery className="w-5 h-5 text-green-600" />}
                  <div>
                    <CardTitle className="text-lg">{device.name}</CardTitle>
                    <p className="text-xs text-gray-500">{device.id}</p>
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
            <CardContent className="space-y-3">
              {device.metrics.battery_level !== undefined && (
                <div className="flex justify-between text-sm"><span className="text-gray-600">Battery</span><span className="font-semibold">{device.metrics.battery_level.toFixed(0)}%</span></div>
              )}
              {device.metrics.power_output !== undefined && (
                <div className="flex justify-between text-sm"><span className="text-gray-600">Output</span><span className="font-semibold">{device.metrics.power_output.toFixed(0)}W</span></div>
              )}
              {device.metrics.signal_strength !== undefined && (
                <div className="flex justify-between text-sm"><span className="text-gray-600">Signal</span><span className="font-semibold">{device.metrics.signal_strength.toFixed(0)}%</span></div>
              )}
              <div className="border-t pt-2 text-xs text-gray-500">Last seen: {new Date(device.last_seen).toLocaleString()}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {devices.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-gray-500">
            <Activity className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold mb-2">No Devices</h3>
            <p>We couldn't load any monitoring data yet.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}