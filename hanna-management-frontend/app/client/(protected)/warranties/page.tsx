'use client';

import { useEffect, useState } from 'react';
import { FiShield, FiAlertCircle, FiRefreshCw, FiFilter } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import { DownloadWarrantyCertificateButton } from '@/app/components/shared/DownloadButtons';

interface Warranty {
  id: number;
  serialized_item_serial?: string;
  product_name?: string;
  manufacturer_name?: string;
  start_date?: string;
  end_date?: string;
  status?: string;
  warranty_period_months?: number;
  created_at?: string;
}

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-32"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-28"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-16"></div>
    </td>
  </tr>
);

export default function ClientWarrantiesPage() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const { accessToken } = useAuthStore();

  const fetchWarranties = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/client/warranties/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Unauthorized. Please log in again.');
        } else if (response.status === 404) {
          throw new Error('Warranties endpoint not found.');
        }
        throw new Error(`Failed to fetch warranties (${response.status})`);
      }

      const result = await response.json();
      setWarranties(result.results || result || []);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching warranties');
      console.error('Warranty fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchWarranties();
    }
  }, [accessToken]);

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleError = (message: string) => {
    setErrorMessage(message);
    setTimeout(() => setErrorMessage(null), 3000);
  };

  const getStatusBadgeClass = (status?: string) => {
    const statusMap: Record<string, string> = {
      active: 'bg-green-100 text-green-800',
      expired: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800',
      cancelled: 'bg-gray-100 text-gray-800',
    };
    return statusMap[status || ''] || 'bg-gray-100 text-gray-800';
  };

  const filteredWarranties = warranties
    .filter(w => statusFilter === 'all' || w.status === statusFilter)
    .filter(w => 
      searchQuery === '' || 
      (w.product_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (w.manufacturer_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (w.serialized_item_serial || '').toLowerCase().includes(searchQuery.toLowerCase())
    );

  const stats = {
    total: warranties.length,
    active: warranties.filter(w => w.status === 'active').length,
    expired: warranties.filter(w => w.status === 'expired').length,
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <FiShield className="h-8 w-8 text-green-600" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">My Warranties</h1>
        </div>
        <p className="text-sm text-gray-600">
          View and download certificates for your product warranties.
        </p>
      </div>

      {/* Stats Cards */}
      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm font-medium">Total Warranties</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
            <p className="text-gray-600 text-sm font-medium">Active</p>
            <p className="text-2xl font-bold text-green-600 mt-1">{stats.active}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
            <p className="text-gray-600 text-sm font-medium">Expired</p>
            <p className="text-2xl font-bold text-red-600 mt-1">{stats.expired}</p>
          </div>
        </div>
      )}

      {/* Messages */}
      {successMessage && (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded-md flex items-center gap-3">
          <span className="text-lg">✓</span>
          {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="mb-4 p-4 bg-orange-100 border border-orange-400 text-orange-700 rounded-md flex items-center gap-3">
          <FiAlertCircle className="h-5 w-5" />
          {errorMessage}
        </div>
      )}
      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
          <div className="flex items-center gap-2 mb-1">
            <FiAlertCircle className="h-5 w-5" />
            <span className="font-semibold">Error loading warranties</span>
          </div>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => fetchWarranties()}
            className="mt-2 inline-flex items-center gap-2 px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
          >
            <FiRefreshCw className="h-4 w-4" /> Try Again
          </button>
        </div>
      )}

      {/* Search and Filters */}
      {!loading && warranties.length > 0 && (
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <input
                type="text"
                placeholder="Search by product, manufacturer, or serial..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All Statuses</option>
                <option value="active">Active</option>
                <option value="expired">Expired</option>
                <option value="pending">Pending</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      <div className="mt-4 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                      Product
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Serial Number
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Manufacturer
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Period
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                      Certificate
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {loading ? (
                    <>
                      <SkeletonRow />
                      <SkeletonRow />
                      <SkeletonRow />
                    </>
                  ) : filteredWarranties.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-10">
                        <div className="text-center">
                          <FiShield className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                          <p className="text-sm text-gray-500 font-medium">
                            {searchQuery || statusFilter !== 'all' ? 'No warranties match your search' : 'No warranties found yet'}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            Your product warranties will appear here once registered.
                          </p>
                        </div>
                      </td>
                    </tr>
                  ) : (
                    filteredWarranties.map((warranty) => {
                      const startDate = warranty.start_date ? new Date(warranty.start_date) : null;
                      const endDate = warranty.end_date ? new Date(warranty.end_date) : null;
                      
                      return (
                        <tr key={warranty.id} className="hover:bg-gray-50 transition">
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                            {warranty.product_name || 'N/A'}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 font-mono">
                            {warranty.serialized_item_serial || 'N/A'}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                            {warranty.manufacturer_name || 'N/A'}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                            {startDate && endDate ? (
                              <span className="text-xs">
                                {startDate.toLocaleDateString()} – {endDate.toLocaleDateString()}
                              </span>
                            ) : 'N/A'}
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm">
                            <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(warranty.status)}`}>
                              {warranty.status || 'N/A'}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-3 py-4 text-center">
                            <DownloadWarrantyCertificateButton
                              warrantyId={warranty.id}
                              variant="icon"
                              size="sm"
                              isAdmin={false}
                              onSuccess={handleSuccess}
                              onError={handleError}
                            />
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
