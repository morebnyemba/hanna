'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiPackage, FiRefreshCw, FiAlertCircle, FiCpu } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import StatCard from './StatCard';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';
import { DateRangePicker } from '@/app/components/DateRangePicker';

interface ManufacturerAnalytics {
  warranty_metrics: {
    total_warranty_repairs: number;
    items_pending_collection: number;
    items_replaced: number;
  };
  fault_analytics: {
    overloaded_inverters: number;
    ai_insight_common_faults: string[];
  };
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
  const [data, setData] = useState<ManufacturerAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 29),
    to: new Date(),
  });

  useEffect(() => {
    const fetchData = async () => {
      if (!date?.from || !date?.to) return;

      setLoading(true);
      setError(null);
      try {
        const startDate = date.from.toISOString().split('T')[0];
        const endDate = date.to.toISOString().split('T')[0];
        
        const response = await apiClient.get<ManufacturerAnalytics>(`/crm-api/analytics/manufacturer/?start_date=${startDate}&end_date=${endDate}`);
        setData(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch dashboard data.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [date]);

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Manufacturer Dashboard</h1>
        <DateRangePicker date={date} setDate={setDate} />
      </div>
      
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
            data && (
                <>
                    <StatCard icon={<FiTool size={24} className="text-blue-500" />} title="Total Warranty Repairs" value={data.warranty_metrics?.total_warranty_repairs ?? 0} color="border-blue-500" />
                    <StatCard icon={<FiPackage size={24} className="text-yellow-500" />} title="Items Pending Collection" value={data.warranty_metrics?.items_pending_collection ?? 0} color="border-yellow-500" />
                    <StatCard icon={<FiRefreshCw size={24} className="text-green-500" />} title="Items Replaced" value={data.warranty_metrics?.items_replaced ?? 0} color="border-green-500" />
                    <StatCard icon={<FiAlertCircle size={24} className="text-red-500" />} title="Overloaded Inverters" value={data.fault_analytics?.overloaded_inverters ?? 0} color="border-red-500" />
                </>
            )
        )}
      </div>

      {!loading && !error && data && (
        <div className="mt-8 bg-white p-6 rounded-lg shadow-md border">
            <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center"><FiCpu className="mr-3" /> AI Insight: Common Fault Keywords</h2>
            <div className="flex flex-wrap gap-2">
                {data.fault_analytics?.ai_insight_common_faults.map((fault, index) => (
                    <span key={index} className="bg-blue-100 text-blue-800 text-sm font-medium mr-2 px-2.5 py-0.5 rounded-full">
                        {fault}
                    </span>
                ))}
            </div>
        </div>
      )}
    </main>
  );
}