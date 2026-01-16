'use client';

import { useEffect, useState } from 'react';
import { FiAlertTriangle, FiTrendingDown, FiTrendingUp, FiPackage, FiBarChart2 } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface FaultData {
  product_name: string;
  product_id: string;
  total_installations: number;
  fault_count: number;
  fault_rate: number;
  common_faults: string[];
  trend: 'up' | 'down' | 'stable';
}

interface FaultSummary {
  total_installations: number;
  total_faults: number;
  overall_fault_rate: number;
  high_risk_products: number;
}

export default function AdminFaultRateAnalyticsPage() {
  const [faultData, setFaultData] = useState<FaultData[]>([]);
  const [summary, setSummary] = useState<FaultSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'rate' | 'count'>('rate');
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchFaultAnalytics = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/admin-panel/fault-analytics/?sort_by=${sortBy}`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch fault analytics. Status: ' + response.status);
        }

        const result = await response.json();
        setFaultData(result.products || []);
        setSummary(result.summary || null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchFaultAnalytics();
    }
  }, [accessToken, sortBy]);

  const getFaultRateColor = (rate: number) => {
    if (rate >= 20) return 'text-red-600 bg-red-100';
    if (rate >= 10) return 'text-orange-600 bg-orange-100';
    if (rate >= 5) return 'text-yellow-600 bg-yellow-100';
    return 'text-green-600 bg-green-100';
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'up') return <FiTrendingUp className="text-red-600" />;
    if (trend === 'down') return <FiTrendingDown className="text-green-600" />;
    return <span className="text-gray-400">—</span>;
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
          <FiAlertTriangle className="mr-3 h-8 w-8 text-red-600" />
          Fault Rate Analytics
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Monitor product fault rates and identify problematic equipment.
        </p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Installations</p>
                <p className="text-2xl font-bold text-gray-900">{summary.total_installations}</p>
              </div>
              <FiPackage className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Faults</p>
                <p className="text-2xl font-bold text-red-600">{summary.total_faults}</p>
              </div>
              <FiAlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Overall Fault Rate</p>
                <p className="text-2xl font-bold text-orange-600">{summary.overall_fault_rate.toFixed(2)}%</p>
              </div>
              <FiBarChart2 className="h-8 w-8 text-orange-600" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">High Risk Products</p>
                <p className="text-2xl font-bold text-red-600">{summary.high_risk_products}</p>
              </div>
              <FiAlertTriangle className="h-8 w-8 text-red-600" />
            </div>
          </div>
        </div>
      )}

      {/* Sort Controls */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Product Fault Rates</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('rate')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              sortBy === 'rate'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Sort by Rate
          </button>
          <button
            onClick={() => setSortBy('count')}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              sortBy === 'count'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Sort by Count
          </button>
        </div>
      </div>

      {/* Fault Data Table */}
      {faultData.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiBarChart2 className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No fault data available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Fault analytics will appear here once installations report issues.
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Installations
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Faults
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fault Rate
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Trend
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Common Faults
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {faultData.map((product) => (
                  <tr key={product.product_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FiPackage className="mr-2 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900">{product.product_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.total_installations}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-medium">
                      {product.fault_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getFaultRateColor(product.fault_rate)}`}>
                        {product.fault_rate.toFixed(2)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getTrendIcon(product.trend)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {product.common_faults.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {product.common_faults.slice(0, 3).map((fault, idx) => (
                            <span key={idx} className="inline-block px-2 py-1 bg-gray-100 rounded text-xs">
                              {fault}
                            </span>
                          ))}
                          {product.common_faults.length > 3 && (
                            <span className="inline-block px-2 py-1 bg-gray-100 rounded text-xs">
                              +{product.common_faults.length - 3} more
                            </span>
                          )}
                        </div>
                      ) : (
                        <span className="text-gray-400">No data</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
