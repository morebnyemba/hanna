'use client';

import { useEffect, useState } from 'react';
import { FiBox, FiAlertTriangle, FiCheckCircle, FiClock } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface ManufacturerStats {
  total_orders: number;
  pending_orders: number;
  completed_orders: number;
  warranty_claims: number;
}

const StatCard = ({ icon, title, value, color }: { icon: React.ReactNode, title: string, value: number, color: string }) => (
  <div className={`bg-white p-6 rounded-lg shadow-md border-l-4 ${color}`}>
    <div className="flex items-center">
      <div className="mr-4">{icon}</div>
      <div>
        <p className="text-sm font-medium text-gray-500 uppercase">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  </div>
);

export default function ManufacturerDashboardPage() {
  const [stats, setStats] = useState<ManufacturerStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<ManufacturerStats>('/crm-api/manufacturer/dashboard-stats/');
        setStats(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch dashboard statistics.');
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <main className="flex-1 p-8 overflow-y-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Manufacturer Dashboard</h1>
      {loading && <p className="text-center text-gray-500">Loading statistics...</p>}
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
      {!loading && !error && stats && (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard icon={<FiBox size={24} className="text-blue-500" />} title="Total Orders" value={stats?.total_orders ?? 0} color="border-blue-500" />
        <StatCard icon={<FiClock size={24} className="text-yellow-500" />} title="Pending Orders" value={stats?.pending_orders ?? 0} color="border-yellow-500" />
        <StatCard icon={<FiCheckCircle size={24} className="text-green-500" />} title="Completed Orders" value={stats?.completed_orders ?? 0} color="border-green-500" />
        <StatCard icon={<FiAlertTriangle size={24} className="text-red-500" />} title="Warranty Claims" value={stats?.warranty_claims ?? 0} color="border-red-500" />
      </div>
      )}
      {/* We can add more components here like recent orders list, charts, etc. */}
    </main>
  );
}