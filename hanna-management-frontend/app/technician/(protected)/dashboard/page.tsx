'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiCheckCircle, FiClock } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { JobCard } from '@/app/types';

interface TechnicianStats {
  assigned_job_cards: number;
  completed_job_cards: number;
  pending_job_cards: number;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: JobCard[];
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

const JobCardList = ({ jobCards }: { jobCards: JobCard[] }) => (
    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200 mt-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Assigned Job Cards</h2>
        <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job Card #</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {jobCards.map((card) => (
                        <tr key={card.job_card_number}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600">{card.job_card_number}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">{card.customer_name}</div>
                                <div className="text-sm text-gray-500">{card.customer_whatsapp}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm text-gray-900">{card.serialized_item?.product_name}</div>
                                <div className="text-sm text-gray-500">SN: {card.serialized_item?.serial_number}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap"><span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full`}>{card.status}</span></td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{card.creation_date}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    </div>
);

export default function TechnicianDashboardPage() {
  const [stats, setStats] = useState<TechnicianStats | null>(null);
  const [jobCards, setJobCards] = useState<JobCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [statsResponse, jobCardsResponse] = await Promise.all([
          apiClient.get<TechnicianStats>('/crm-api/warranty/dashboards/technician/'),
          apiClient.get<PaginatedResponse>('/crm-api/warranty/technician/job-cards/')
        ]);
        setStats(statsResponse.data);
        setJobCards(jobCardsResponse.data.results);
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
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">Technician Dashboard</h1>
      {loading && <p className="text-center text-gray-500">Loading dashboard...</p>}
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
      {!loading && !error && stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          <StatCard icon={<FiTool size={24} className="text-blue-500" />} title="Assigned Job Cards" value={stats?.assigned_job_cards ?? 0} color="border-blue-500" />
          <StatCard icon={<FiClock size={24} className="text-yellow-500" />} title="Pending Job Cards" value={stats?.pending_job_cards ?? 0} color="border-yellow-500" />
          <StatCard icon={<FiCheckCircle size={24} className="text-green-500" />} title="Completed Job Cards" value={stats?.completed_job_cards ?? 0} color="border-green-500" />
        </div>
      )}

      {!loading && !error && <JobCardList jobCards={jobCards} />}
    </main>
  );
}
