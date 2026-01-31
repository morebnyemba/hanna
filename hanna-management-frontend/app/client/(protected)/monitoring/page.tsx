"use client";
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuthStore } from '@/app/store/authStore';
import { Activity, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

interface Installation {
  id: string;
  short_id: string;
  installation_type: string;
  system_size: number;
  capacity_unit: string;
  installation_address: string;
  installation_status: string;
  installation_date: string;
}

export default function ClientMonitoringPage() {
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
      console.error('Fetch error:', err);
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
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading monitoring data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <Activity className="w-8 h-8 text-purple-600" />
            System Monitoring
          </h1>
          <p className="text-gray-600 mt-1">Real-time status of your installations</p>
        </div>
        <button
          onClick={() => fetchInstallations(true)}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
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

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="h-4 w-4" />Total Systems
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{installations.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />Active
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {installations.filter(i => i.installation_status === 'active').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-600" />Requires Attention
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {installations.filter(i => i.installation_status !== 'active').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Installations Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {installations.map(installation => (
          <Card key={installation.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{installation.installation_type}</CardTitle>
                  <p className="text-xs text-gray-500 mt-1">{installation.short_id}</p>
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
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-sm text-gray-600">Location</p>
                <p className="font-semibold text-gray-900 text-sm">{installation.installation_address}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-gray-600">System Size</p>
                  <p className="font-semibold text-gray-900">
                    {installation.system_size} {installation.capacity_unit}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-600">Installed</p>
                  <p className="font-semibold text-gray-900">
                    {new Date(installation.installation_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="border-t pt-2">
                <p className="text-xs text-gray-600">Last monitored: Just now</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {installations.length === 0 && !error && (
        <Card>
          <CardContent className="py-12 text-center text-gray-500">
            <Activity className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold mb-2">No Systems</h3>
            <p>No active installations found for monitoring.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}