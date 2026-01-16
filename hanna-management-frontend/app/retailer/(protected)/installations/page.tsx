'use client';

import { useEffect, useState } from 'react';
import { FiPackage, FiMapPin, FiCalendar, FiUser, FiCheckCircle, FiClock, FiAlertCircle } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Installation {
  id: string;
  customer_name: string;
  installation_type: string;
  installation_status: string;
  system_size: number;
  capacity_unit: string;
  installation_address: string;
  installation_date: string | null;
  commissioning_date: string | null;
  order_id: string | null;
  created_at: string;
}

export default function RetailerInstallationsPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchInstallations = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/users/retailer/installations/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch installations. Status: ${response.status}`);
        }

        const result = await response.json();
        setInstallations(result.results || result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchInstallations();
    }
  }, [accessToken]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: <FiClock className="mr-1" />, text: 'Pending' },
      in_progress: { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: <FiClock className="mr-1" />, text: 'In Progress' },
      commissioned: { color: 'bg-green-100 text-green-800 border-green-200', icon: <FiCheckCircle className="mr-1" />, text: 'Commissioned' },
      active: { color: 'bg-green-100 text-green-800 border-green-200', icon: <FiCheckCircle className="mr-1" />, text: 'Active' },
      decommissioned: { color: 'bg-gray-100 text-gray-800 border-gray-200', icon: <FiAlertCircle className="mr-1" />, text: 'Decommissioned' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${config.color}`}>
        {config.icon}
        {config.text}
      </span>
    );
  };

  const filteredInstallations = installations.filter(installation => {
    if (filter === 'all') return true;
    return installation.installation_status === filter;
  });

  const statusCounts = {
    all: installations.length,
    pending: installations.filter(i => i.installation_status === 'pending').length,
    in_progress: installations.filter(i => i.installation_status === 'in_progress').length,
    commissioned: installations.filter(i => i.installation_status === 'commissioned' || i.installation_status === 'active').length,
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiPackage className="mr-3 h-8 w-8 text-blue-600" />
          Installation Tracking
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Track the status of installations for your customer orders.
        </p>
      </div>

      {/* Status Filter Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <button
          onClick={() => setFilter('all')}
          className={`p-4 rounded-lg border-2 transition-all ${
            filter === 'all'
              ? 'bg-blue-50 border-blue-500'
              : 'bg-white border-gray-200 hover:border-blue-300'
          }`}
        >
          <div className="text-2xl font-bold text-gray-900">{statusCounts.all}</div>
          <div className="text-sm text-gray-600">All Installations</div>
        </button>

        <button
          onClick={() => setFilter('pending')}
          className={`p-4 rounded-lg border-2 transition-all ${
            filter === 'pending'
              ? 'bg-yellow-50 border-yellow-500'
              : 'bg-white border-gray-200 hover:border-yellow-300'
          }`}
        >
          <div className="text-2xl font-bold text-yellow-600">{statusCounts.pending}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </button>

        <button
          onClick={() => setFilter('in_progress')}
          className={`p-4 rounded-lg border-2 transition-all ${
            filter === 'in_progress'
              ? 'bg-blue-50 border-blue-500'
              : 'bg-white border-gray-200 hover:border-blue-300'
          }`}
        >
          <div className="text-2xl font-bold text-blue-600">{statusCounts.in_progress}</div>
          <div className="text-sm text-gray-600">In Progress</div>
        </button>

        <button
          onClick={() => setFilter('commissioned')}
          className={`p-4 rounded-lg border-2 transition-all ${
            filter === 'commissioned'
              ? 'bg-green-50 border-green-500'
              : 'bg-white border-gray-200 hover:border-green-300'
          }`}
        >
          <div className="text-2xl font-bold text-green-600">{statusCounts.commissioned}</div>
          <div className="text-sm text-gray-600">Commissioned</div>
        </button>
      </div>

      {/* Installations List */}
      {filteredInstallations.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiPackage className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No installations found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {filter === 'all' 
              ? 'Your customer installations will appear here once orders are processed.'
              : `No installations with status "${filter}".`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredInstallations.map((installation) => (
            <div
              key={installation.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                {/* Main Info */}
                <div className="flex-1 mb-4 lg:mb-0">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <FiUser className="mr-2 text-gray-400" />
                        {installation.customer_name}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {installation.installation_type?.replace('_', ' ').toUpperCase()} - {installation.system_size} {installation.capacity_unit}
                      </p>
                    </div>
                    <div className="ml-4">
                      {getStatusBadge(installation.installation_status)}
                    </div>
                  </div>

                  <div className="mt-3 space-y-2">
                    {installation.installation_address && (
                      <div className="flex items-center text-sm text-gray-600">
                        <FiMapPin className="mr-2 text-gray-400" />
                        {installation.installation_address}
                      </div>
                    )}
                    
                    <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                      {installation.installation_date && (
                        <div className="flex items-center">
                          <FiCalendar className="mr-2 text-gray-400" />
                          <span>Installed: {new Date(installation.installation_date).toLocaleDateString()}</span>
                        </div>
                      )}
                      {installation.commissioning_date && (
                        <div className="flex items-center">
                          <FiCheckCircle className="mr-2 text-green-500" />
                          <span>Commissioned: {new Date(installation.commissioning_date).toLocaleDateString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Order Reference */}
                {installation.order_id && (
                  <div className="lg:ml-6 pt-4 lg:pt-0 border-t lg:border-t-0 lg:border-l lg:pl-6">
                    <div className="text-sm text-gray-500">Order ID</div>
                    <div className="text-sm font-mono text-gray-900 mt-1">
                      {installation.order_id.slice(0, 8)}...
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
