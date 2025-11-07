'use client';

import { useEffect, useState } from 'react';
import { FiBox, FiAlertTriangle, FiCheckCircle, FiClock } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import StatCard from './StatCard';
import RecentClaimsTable from './RecentClaimsTable';

interface ManufacturerStats {
  total_orders: number;
  pending_orders: number;
  completed_orders: number;
  warranty_claims: number;
}

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

interface PaginatedClaimsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WarrantyClaim[];
}

const StatCardSkeleton = () => (
    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border-l-4 border-gray-200 animate-pulse">
        <div className="flex items-center">
            <div className="mr-3 sm:mr-4">
                <div className="h-8 w-8 bg-gray-200 rounded-full"></div>
            </div>
            <div>
                <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-12"></div>
            </div>
        </div>
    </div>
);

export default function ManufacturerDashboardPage() {
  const [stats, setStats] = useState<ManufacturerStats | null>(null);
  const [claims, setClaims] = useState<WarrantyClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [statsResponse, claimsResponse] = await Promise.all([
          apiClient.get<ManufacturerStats>('/crm-api/manufacturer/dashboard-stats/'),
          apiClient.get<PaginatedClaimsResponse>('/crm-api/manufacturer/warranty-claims/?page_size=5')
        ]);
        setStats(statsResponse.data);
        setClaims(claimsResponse.data.results);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">Manufacturer Dashboard</h1>
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        {loading ? (
            <>
                <StatCardSkeleton />
                <StatCardSkeleton />
                <StatCardSkeleton />
                <StatCardSkeleton />
            </>
        ) : (
            stats && (
                <>
                    <StatCard icon={<FiBox size={24} className="text-blue-500" />} title="Total Orders" value={stats?.total_orders ?? 0} color="border-blue-500" />
                    <StatCard icon={<FiClock size={24} className="text-yellow-500" />} title="Pending Orders" value={stats?.pending_orders ?? 0} color="border-yellow-500" />
                    <StatCard icon={<FiCheckCircle size={24} className="text-green-500" />} title="Completed Orders" value={stats?.completed_orders ?? 0} color="border-green-500" />
                    <StatCard icon={<FiAlertTriangle size={24} className="text-red-500" />} title="Warranty Claims" value={stats?.warranty_claims ?? 0} color="border-red-500" />
                </>
            )
        )}
        </div>

      {!loading && !error && <RecentClaimsTable claims={claims} />}
    </main>
  );
}