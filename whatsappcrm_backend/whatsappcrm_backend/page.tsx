'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiUsers, FiMessageSquare, FiAlertCircle, FiShield, FiTool, FiCheckCircle } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

// --- Types to match the backend API response ---
interface DashboardData {
  total_users: number;
  total_customers: number;
  total_warranties: number;
  active_warranties: number;
  total_claims: number;
  pending_claims: number;
  open_job_cards: number;
}

interface ActivityLogItem {
  id: string;
  timestamp: string;
  iconName: string;
  iconColor: string;
}

interface DashboardData {
  stats_cards: StatsCards;
  recent_activity_log: ActivityLogItem[];
}

// --- Reusable Stat Card Component ---
const StatCard = ({ title, value, icon: Icon }: { title: string; value: string | number; icon: React.ElementType }) => (
  <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
    <div className="flex items-center">
      <div className="p-3 bg-gray-100 rounded-full">
        <Icon className="h-6 w-6 text-gray-600" />
      </div>
      <div className="ml-4">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      </div>
    </div>
  </div>
);

// --- Main Dashboard Page Component ---
export default function AdminDashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken, logout } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/admin/dashboard-stats/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          if (response.status === 401) handleLogout();
          throw new Error(`Failed to fetch data. Status: ${response.status}`);
        }

        const result: DashboardData = await response.json();
        setData(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchData();
    }
  }, [accessToken]);

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  if (loading) {
    return <div className="flex min-h-screen items-center justify-center bg-gray-50"><p>Loading Dashboard...</p></div>;
  }

  if (error) {
    return <div className="flex min-h-screen items-center justify-center bg-gray-50"><p className="text-red-500">Error: {error}</p></div>;
  }

  if (!data) return <div className="flex min-h-screen items-center justify-center bg-gray-50"><p>No data available.</p></div>;

  const { stats_cards, recent_activity_log } = data;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <main className="p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Admin Analytics Dashboard</h1>
          <button onClick={handleLogout} className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700">
            Logout
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <StatCard title="Active Warranties" value={stats_cards.active_warranties} icon={FiShield} />
          <StatCard title="Pending Warranty Claims" value={stats_cards.pending_warranty_claims} icon={FiAlertCircle} />
          <StatCard title="Open Job Cards" value={stats_cards.open_job_cards} icon={FiTool} />
          <StatCard title="Total Contacts" value={stats_cards.total_contacts} icon={FiUsers} />
          <StatCard title="Active Conversations" value={stats_cards.active_conversations_count} icon={FiMessageSquare} />
          <StatCard title="New Contacts Today" value={stats_cards.new_contacts_today} icon={FiCheckCircle} />
        </div>
      </main>
    </div>
  );
}