'use client';

import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Zap, TrendingUp, Sun, Battery, Calendar } from 'lucide-react';

interface EnergyData {
  time: string;
  production: number;
  consumption: number;
  battery: number;
  gridExport: number;
}

// Generate sample energy data for the past 24 hours
const generateHourlyData = (): EnergyData[] => {
  const data: EnergyData[] = [];
  const now = new Date();
  
  for (let i = 23; i >= 0; i--) {
    const hour = new Date(now.getTime() - i * 3600000);
    const hourNum = hour.getHours();
    
    // Solar production peaks at midday
    const solarFactor = Math.max(0, Math.sin((hourNum - 6) * Math.PI / 12));
    const production = Math.floor(solarFactor * 4500 + Math.random() * 500);
    
    // Consumption varies throughout the day
    const consumptionBase = hourNum >= 6 && hourNum <= 22 ? 2000 : 800;
    const consumption = Math.floor(consumptionBase + Math.random() * 1000);
    
    // Battery level based on production vs consumption
    const battery = Math.min(100, Math.max(20, 50 + (production - consumption) / 100 + Math.random() * 10));
    
    // Grid export when production exceeds consumption
    const gridExport = Math.max(0, production - consumption);
    
    data.push({
      time: hour.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      production,
      consumption,
      battery: Math.floor(battery),
      gridExport,
    });
  }
  
  return data;
};

// Generate weekly data
const generateWeeklyData = (): EnergyData[] => {
  const data: EnergyData[] = [];
  const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  const now = new Date();
  
  for (let i = 6; i >= 0; i--) {
    const day = new Date(now.getTime() - i * 86400000);
    const dayName = days[day.getDay()];
    
    // Weather factor (random sunny/cloudy days)
    const weatherFactor = 0.5 + Math.random() * 0.5;
    
    data.push({
      time: dayName,
      production: Math.floor(25000 * weatherFactor + Math.random() * 5000),
      consumption: Math.floor(18000 + Math.random() * 4000),
      battery: Math.floor(60 + Math.random() * 30),
      gridExport: Math.floor(5000 * weatherFactor + Math.random() * 3000),
    });
  }
  
  return data;
};

// Generate monthly data
const generateMonthlyData = (): EnergyData[] => {
  const data: EnergyData[] = [];
  const now = new Date();
  
  for (let i = 29; i >= 0; i--) {
    const day = new Date(now.getTime() - i * 86400000);
    
    // Weather and seasonal factors
    const weatherFactor = 0.4 + Math.random() * 0.6;
    
    data.push({
      time: day.getDate().toString(),
      production: Math.floor(28000 * weatherFactor + Math.random() * 5000),
      consumption: Math.floor(20000 + Math.random() * 5000),
      battery: Math.floor(55 + Math.random() * 35),
      gridExport: Math.floor(6000 * weatherFactor + Math.random() * 4000),
    });
  }
  
  return data;
};

type TimeRange = '24h' | '7d' | '30d';

export default function EnergyProductionChart() {
  const [timeRange, setTimeRange] = useState<TimeRange>('24h');
  const [data, setData] = useState<EnergyData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      switch (timeRange) {
        case '24h':
          setData(generateHourlyData());
          break;
        case '7d':
          setData(generateWeeklyData());
          break;
        case '30d':
          setData(generateMonthlyData());
          break;
      }
      setLoading(false);
    }, 500);
  }, [timeRange]);

  // Calculate totals
  const totalProduction = data.reduce((sum, d) => sum + d.production, 0);
  const totalConsumption = data.reduce((sum, d) => sum + d.consumption, 0);
  const totalExport = data.reduce((sum, d) => sum + d.gridExport, 0);
  const avgBattery = data.length > 0 ? data.reduce((sum, d) => sum + d.battery, 0) / data.length : 0;

  // Format energy values
  const formatEnergy = (watts: number) => {
    if (watts >= 1000000) return `${(watts / 1000000).toFixed(1)} MWh`;
    if (watts >= 1000) return `${(watts / 1000).toFixed(1)} kWh`;
    return `${watts} Wh`;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle className="flex items-center gap-2">
            <Sun className="w-5 h-5 text-yellow-500" />
            Energy Production History
          </CardTitle>
          <div className="flex gap-2">
            {(['24h', '7d', '30d'] as TimeRange[]).map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange(range)}
              >
                {range === '24h' ? '24 Hours' : range === '7d' ? '7 Days' : '30 Days'}
              </Button>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-yellow-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-yellow-700 mb-1">
              <Sun className="w-4 h-4" />
              Production
            </div>
            <div className="text-xl font-bold text-yellow-800">{formatEnergy(totalProduction)}</div>
          </div>
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-blue-700 mb-1">
              <Zap className="w-4 h-4" />
              Consumption
            </div>
            <div className="text-xl font-bold text-blue-800">{formatEnergy(totalConsumption)}</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-green-700 mb-1">
              <TrendingUp className="w-4 h-4" />
              Grid Export
            </div>
            <div className="text-xl font-bold text-green-800">{formatEnergy(totalExport)}</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm text-purple-700 mb-1">
              <Battery className="w-4 h-4" />
              Avg Battery
            </div>
            <div className="text-xl font-bold text-purple-800">{avgBattery.toFixed(0)}%</div>
          </div>
        </div>

        {/* Main Chart */}
        {loading ? (
          <div className="h-80 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500"></div>
          </div>
        ) : (
          <div style={{ width: '100%', height: 320 }}>
            <ResponsiveContainer>
              <AreaChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorProduction" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#eab308" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorConsumption" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="time" stroke="#6b7280" fontSize={11} tickLine={false} />
                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} tickFormatter={(val) => `${(val / 1000).toFixed(0)}kW`} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    borderRadius: '0.5rem',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                  }}
                  formatter={(value: number, name: string) => [
                    `${(value / 1000).toFixed(2)} kWh`,
                    name.charAt(0).toUpperCase() + name.slice(1)
                  ]}
                />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="production"
                  name="Production"
                  stroke="#eab308"
                  strokeWidth={2}
                  fill="url(#colorProduction)"
                />
                <Area
                  type="monotone"
                  dataKey="consumption"
                  name="Consumption"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  fill="url(#colorConsumption)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Battery Level Chart */}
        {!loading && (
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <Battery className="w-4 h-4" />
              Battery Level Over Time
            </h4>
            <div style={{ width: '100%', height: 120 }}>
              <ResponsiveContainer>
                <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="time" stroke="#6b7280" fontSize={10} tickLine={false} />
                  <YAxis stroke="#6b7280" fontSize={10} tickLine={false} domain={[0, 100]} tickFormatter={(val) => `${val}%`} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      borderRadius: '0.5rem',
                      border: '1px solid #e5e7eb',
                    }}
                    formatter={(value: number) => [`${value}%`, 'Battery']}
                  />
                  <Line
                    type="monotone"
                    dataKey="battery"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
