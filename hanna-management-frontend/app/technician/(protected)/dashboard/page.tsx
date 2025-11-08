'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiCheckCircle, FiClock, FiClipboard, FiHardDrive } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { DateRange } from 'react-day-picker';
import { subDays } from 'date-fns';
import { DateRangePicker } from '@/app/components/DateRangePicker';

interface TechnicianAnalytics {
  repair_metrics: {
    my_open_job_cards: number;
    my_completed_jobs_in_period: number;
  };
  installation_metrics: {
    my_total_installations_in_period: number;
    my_pending_installations: number;
  };
}

const StatCard = ({ icon, title, value, color }: { icon: React.ReactNode; title: string; value: number; color: string; }) => (
    <div className={`bg-white p-4 sm:p-6 rounded-lg shadow-md border-l-4 ${color}`}>
        <div className="flex items-center">
            <div className="mr-3 sm:mr-4">
                {icon}
            </div>
            <div>
                <p className="text-sm font-medium text-gray-600">{title}</p>
                <p className="text-2xl font-bold text-gray-900">{value}</p>
            </div>
        </div>
    </div>
);

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

export default function TechnicianDashboardPage() {
  const [data, setData] = useState<TechnicianAnalytics | null>(null);
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
        
        const response = await apiClient.get<TechnicianAnalytics>(`/crm-api/analytics/technician/?start_date=${startDate}&end_date=${endDate}`);
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
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Technician Dashboard</h1>
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
                    <StatCard icon={<FiTool size={24} className="text-red-500" />} title="My Open Job Cards" value={data.repair_metrics?.my_open_job_cards ?? 0} color="border-red-500" />
                    <StatCard icon={<FiCheckCircle size={24} className="text-green-500" />} title="Completed Jobs (Period)" value={data.repair_metrics?.my_completed_jobs_in_period ?? 0} color="border-green-500" />
                    <StatCard icon={<FiClipboard size={24} className="text-yellow-500" />} title="Pending Installations" value={data.installation_metrics?.my_pending_installations ?? 0} color="border-yellow-500" />
                    <StatCard icon={<FiHardDrive size={24} className="text-blue-500" />} title="Total Installations (Period)" value={data.installation_metrics?.my_total_installations_in_period ?? 0} color="border-blue-500" />
                </>
            )
        )}
      </div>
    </main>
  );
}
