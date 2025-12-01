'use client';

import { useEffect, useState } from 'react';
import { FiBox, FiShoppingCart, FiTruck, FiPackage, FiArrowDownCircle, FiArrowUpCircle, FiHome } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import Link from 'next/link';
import { useAuthStore } from '@/app/store/authStore';

interface BranchDashboard {
  branch_name: string | null;
  retailer_name: string | null;
  total_items: number;
  items_in_stock: number;
  items_sold: number;
  items_in_transit: number;
  recent_checkouts: Array<{
    product_name: string;
    serial_number: string;
    status_display: string;
  }>;
  recent_checkins: Array<{
    product_name: string;
    serial_number: string;
    status_display: string;
  }>;
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

export default function BranchDashboardPage() {
  const [data, setData] = useState<BranchDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { selectedRetailer } = useAuthStore();

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<BranchDashboard>('/crm-api/products/retailer-branch/dashboard/');
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
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Branch Dashboard</h1>
          {/* Show selected retailer from login */}
          {selectedRetailer && (
            <p className="text-emerald-600 mt-1 flex items-center">
              <FiHome className="mr-1" />
              Logged in under: <span className="font-semibold ml-1">{selectedRetailer.company_name}</span>
            </p>
          )}
          {data?.branch_name && (
            <p className="text-gray-600 mt-1">
              {data.branch_name} {data.retailer_name && `• ${data.retailer_name}`}
            </p>
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
                icon={<FiPackage size={24} className="text-blue-500" />} 
                title="Total Items" 
                value={data.total_items ?? 0} 
                color="border-blue-500" 
              />
              <StatCard 
                icon={<FiBox size={24} className="text-green-500" />} 
                title="In Stock" 
                value={data.items_in_stock ?? 0} 
                color="border-green-500" 
              />
              <StatCard 
                icon={<FiShoppingCart size={24} className="text-yellow-500" />} 
                title="Sold" 
                value={data.items_sold ?? 0} 
                color="border-yellow-500" 
              />
              <StatCard 
                icon={<FiTruck size={24} className="text-purple-500" />} 
                title="In Transit" 
                value={data.items_in_transit ?? 0} 
                color="border-purple-500" 
              />
            </>
          )
        )}
      </div>

      {/* Quick Actions */}
      <div className="bg-white p-6 rounded-lg shadow-md border mb-8">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link href="/retailer-branch/check-in-out" 
            className="flex items-center p-4 bg-emerald-50 rounded-lg hover:bg-emerald-100 transition-colors">
            <FiArrowUpCircle className="h-8 w-8 text-emerald-600 mr-3" />
            <div>
              <h3 className="font-semibold text-gray-800">Checkout Item</h3>
              <p className="text-sm text-gray-600">Send item to customer</p>
            </div>
          </Link>
          <Link href="/retailer-branch/check-in-out" 
            className="flex items-center p-4 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors">
            <FiArrowDownCircle className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <h3 className="font-semibold text-gray-800">Check-in Item</h3>
              <p className="text-sm text-gray-600">Receive new stock</p>
            </div>
          </Link>
          <Link href="/retailer-branch/inventory" 
            className="flex items-center p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors">
            <FiBox className="h-8 w-8 text-purple-600 mr-3" />
            <div>
              <h3 className="font-semibold text-gray-800">View Inventory</h3>
              <p className="text-sm text-gray-600">Browse all items</p>
            </div>
          </Link>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Checkouts */}
        <div className="bg-white p-6 rounded-lg shadow-md border">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <FiArrowUpCircle className="mr-2 text-emerald-500" /> Recent Checkouts
          </h2>
          {!loading && data?.recent_checkouts && data.recent_checkouts.length > 0 ? (
            <div className="space-y-3">
              {data.recent_checkouts.map((item, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-800">{item.product_name}</p>
                    <p className="text-sm text-gray-500">SN: {item.serial_number}</p>
                  </div>
                  <span className="text-sm text-emerald-600">{item.status_display}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No recent checkouts</p>
          )}
        </div>

        {/* Recent Check-ins */}
        <div className="bg-white p-6 rounded-lg shadow-md border">
          <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <FiArrowDownCircle className="mr-2 text-blue-500" /> Recent Check-ins
          </h2>
          {!loading && data?.recent_checkins && data.recent_checkins.length > 0 ? (
            <div className="space-y-3">
              {data.recent_checkins.map((item, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-800">{item.product_name}</p>
                    <p className="text-sm text-gray-500">SN: {item.serial_number}</p>
                  </div>
                  <span className="text-sm text-blue-600">{item.status_display}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No recent check-ins</p>
          )}
        </div>
      </div>
    </main>
  );
}
