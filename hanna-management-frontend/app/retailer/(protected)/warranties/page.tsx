'use client';

import { useEffect, useState } from 'react';
import { FiShield, FiCheck, FiClock, FiPackage, FiCalendar } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Warranty {
  id: string;
  installation_id: string;
  customer_name: string;
  product_name: string;
  serial_number: string;
  warranty_type: string;
  warranty_period_months: number;
  start_date: string | null;
  end_date: string | null;
  status: string;
  can_activate: boolean;
}

export default function RetailerWarrantiesPage() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('pending');
  const [activating, setActivating] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  const fetchWarranties = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/users/retailer/warranties/?status=${filter}`, {
        headers: {
          'Authorization': `******
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch warranties. Status: ${response.status}`);
      }

      const result = await response.json();
      setWarranties(result.results || result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchWarranties();
    }
  }, [accessToken, filter]);

  const handleActivate = async (warrantyId: string) => {
    if (!confirm('Activate this warranty? This action cannot be undone.')) return;

    setActivating(warrantyId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/users/retailer/warranties/${warrantyId}/activate/`, {
        method: 'POST',
        headers: {
          'Authorization': `******
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to activate warranty');
      }

      alert('Warranty activated successfully!');
      await fetchWarranties();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setActivating(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', text: 'Pending Activation' },
      active: { color: 'bg-green-100 text-green-800', text: 'Active' },
      expired: { color: 'bg-red-100 text-red-800', text: 'Expired' },
      claimed: { color: 'bg-blue-100 text-blue-800', text: 'Claimed' },
    };
    const config = statusConfig[status] || statusConfig.pending;
    return <span className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${config.color}`}>{config.text}</span>;
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
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
          <FiShield className="mr-3 h-8 w-8 text-blue-600" />
          Warranty Management
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Activate and manage warranties for customer installations.
        </p>
      </div>

      {/* Status Filter Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { key: 'pending', label: 'Pending Activation' },
            { key: 'active', label: 'Active' },
            { key: 'expired', label: 'Expired' },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                filter === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Warranties List */}
      {warranties.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiShield className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No warranties found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No {filter} warranties at this time.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {warranties.map((warranty) => (
            <div
              key={warranty.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                {/* Warranty Info */}
                <div className="flex-1 mb-4 lg:mb-0">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <FiPackage className="mr-2 text-gray-400" />
                        {warranty.product_name}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Customer: {warranty.customer_name}
                      </p>
                    </div>
                    <div className="ml-4">
                      {getStatusBadge(warranty.status)}
                    </div>
                  </div>

                  <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-gray-500">Serial Number</p>
                      <p className="text-gray-900 font-medium font-mono">{warranty.serial_number}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Warranty Type</p>
                      <p className="text-gray-900 font-medium capitalize">{warranty.warranty_type.replace('_', ' ')}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Period</p>
                      <p className="text-gray-900 font-medium">{warranty.warranty_period_months} months</p>
                    </div>
                    {warranty.start_date && (
                      <div>
                        <p className="text-gray-500">Valid Until</p>
                        <p className="text-gray-900 font-medium flex items-center">
                          <FiCalendar className="mr-1" />
                          {new Date(warranty.end_date!).toLocaleDateString()}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Actions */}
                {warranty.can_activate && warranty.status === 'pending' && (
                  <div className="lg:ml-6 pt-4 lg:pt-0 border-t lg:border-t-0 lg:border-l lg:pl-6">
                    <button
                      onClick={() => handleActivate(warranty.id)}
                      disabled={activating === warranty.id}
                      className="w-full lg:w-auto bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-2 px-6 rounded-lg flex items-center justify-center transition-colors"
                    >
                      {activating === warranty.id ? (
                        <>
                          <FiClock className="mr-2 animate-spin" />
                          Activating...
                        </>
                      ) : (
                        <>
                          <FiCheck className="mr-2" />
                          Activate Warranty
                        </>
                      )}
                    </button>
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
