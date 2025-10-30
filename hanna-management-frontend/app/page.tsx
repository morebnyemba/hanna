'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiUsers, FiMessageSquare, FiAlertCircle, FiShield, FiTool, FiCheckCircle } from 'react-icons/fi';
import { useAuth } from '../context/AuthContext';

// --- Types to match the backend API response ---
interface StatsCards {
  active_conversations_count: number;
  new_contacts_today: number;
  total_contacts: number;
  pending_human_handovers: number;
  active_warranties: number;
  pending_warranty_claims: number;
  open_job_cards: number;
}

interface ActivityLogItem {
  id: string;
  text: string;
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
export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken, isLoading: isAuthLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // If auth is still loading, wait.
    if (isAuthLoading) {
      return;
    }

    // If not authenticated, redirect to login.
    if (!accessToken) {
      router.push('/login');
      return;
    }

    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

        const response = await fetch(`${apiUrl}/crm-api/stats/dashboard/summary/`, { // Use the accessToken from context
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          // Handle different error statuses if needed
          if (response.status === 401) {
            // Token might be expired, log out the user.
            logout();
          }
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

    fetchData();
  }, [accessToken, isAuthLoading, router, logout]);

  if (loading || isAuthLoading) {
    return <div className="flex min-h-screen items-center justify-center bg-gray-50"><p>Loading Dashboard...</p></div>;
  }

  if (error && accessToken) { // Only show error if the user is supposed to be logged in
    return <div className="flex min-h-screen items-center justify-center bg-gray-50"><p className="text-red-500">Error: {error}</p></div>;
  }

  if (!data) {
    return <div className="flex min-h-screen items-center justify-center bg-gray-50"><p>No data available.</p></div>;
  }

  const { stats_cards, recent_activity_log } = data;

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      <main className="p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Overall Analytics Dashboard</h1>
          <button onClick={logout} className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700">
            Logout
          </button>
        </div>

        {/* Stats Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Displaying a mix of old and new stats */}
          <StatCard title="Active Warranties" value={stats_cards.active_warranties} icon={FiShield} />
          <StatCard title="Pending Warranty Claims" value={stats_cards.pending_warranty_claims} icon={FiAlertCircle} />
          <StatCard title="Open Job Cards" value={stats_cards.open_job_cards} icon={FiTool} />
          <StatCard title="Total Contacts" value={stats_cards.total_contacts} icon={FiUsers} />
          <StatCard title="Active Conversations" value={stats_cards.active_conversations_count} icon={FiMessageSquare} />
          <StatCard title="New Contacts Today" value={stats_cards.new_contacts_today} icon={FiCheckCircle} />
        </div>

        {/* Recent Activity Section */}
        <div className="mt-10">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Recent Activity</h2>
          <div className="bg-white p-4 rounded-lg shadow-md border border-gray-200">
            <ul className="divide-y divide-gray-200">
              {recent_activity_log.map((item) => (
                <li key={item.id} className="py-3 flex items-center">
                  {/* You can add dynamic icons here later */}
                  <div className="ml-3">
                    <p className="text-sm text-gray-800">{item.text}</p>
                    <p className="text-xs text-gray-500">{new Date(item.timestamp).toLocaleString()}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}
