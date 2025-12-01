'use client';

import { useEffect, useState } from 'react';
import { FiGitBranch, FiBox, FiShoppingCart, FiUsers } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import Link from 'next/link';

interface RetailerDashboard {
  company_name: string;
  total_branches: number;
  active_branches: number;
  total_items_across_branches: number;
  total_items_sold: number;
}

const StatCard = ({ icon, title, value, color }: { icon: React.ReactNode; title: string; value: number | string; color: string }) => (
  <div className={`bg-white p-4 sm:p-6 rounded-lg shadow-md border-l-4 ${color}`}>
    <div className="flex items-center">
      <div className="mr-3 sm:mr-4">
        {icon}
      </div>
      <div>
        <p className="text-sm text-gray-500 font-medium">{title}</p>
        <p className="text-2xl font-bold text-gray-800">{value}</p>
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

export default function RetailerDashboardPage() {
  const [data, setData] = useState<RetailerDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<RetailerDashboard>('/crm-api/products/retailer/dashboard/');
        setData(response.data);
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
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Retailer Dashboard</h1>
          {data?.company_name && (
            <p className="text-gray-600 mt-1">{data.company_name}</p>
          )}
        </div>
      </div>
      
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-8">
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
              <StatCard 
                icon={<FiGitBranch size={24} className="text-indigo-500" />} 
                title="Total Branches" 
                value={data.total_branches ?? 0} 
                color="border-indigo-500" 
              />
              <StatCard 
                icon={<FiUsers size={24} className="text-green-500" />} 
                title="Active Branches" 
                value={data.active_branches ?? 0} 
                color="border-green-500" 
              />
              <StatCard 
                icon={<FiBox size={24} className="text-blue-500" />} 
                title="Items Across Branches" 
                value={data.total_items_across_branches ?? 0} 
                color="border-blue-500" 
              />
              <StatCard 
                icon={<FiShoppingCart size={24} className="text-yellow-500" />} 
                title="Total Items Sold" 
                value={data.total_items_sold ?? 0} 
                color="border-yellow-500" 
              />
            </>
          )
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-md border mb-8">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Link href="/retailer/branches" 
            className="flex items-center p-4 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors">
            <FiGitBranch className="h-8 w-8 text-indigo-600 mr-3" />
            <div>
              <h3 className="font-semibold text-gray-800">Manage Branches</h3>
              <p className="text-sm text-gray-600">Add, edit, or deactivate branches</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Info Box */}
      <div className="bg-indigo-50 border border-indigo-200 p-6 rounded-lg">
        <h3 className="font-semibold text-indigo-800 mb-2">📌 Note for Retailers</h3>
        <p className="text-indigo-700">
          As a retailer, you can only manage your branches from this portal. 
          Each branch has its own login and can perform check-in/checkout operations on products.
          Use the <strong>Manage Branches</strong> section to create new branch accounts.
        </p>
      </div>
    </main>
  );
}
