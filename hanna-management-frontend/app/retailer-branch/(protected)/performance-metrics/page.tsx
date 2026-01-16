'use client';

import { useEffect, useState } from 'react';
import { FiBarChart2, FiTrendingUp, FiDownload, FiCalendar, FiCheckCircle, FiClock, FiAlertCircle, FiDollarSign, FiUsers, FiAward, FiTarget } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface Metrics {
  kpis: {
    installations_this_month: number;
    pending_installations: number;
    completed_installations: number;
    customer_complaints: number;
  };
  performance: {
    completion_rate: number;
    average_completion_time_days: number;
    average_satisfaction_rating: number;
  };
  revenue: {
    total_revenue: number;
    installation_count: number;
    average_order_value: number;
  };
  period: {
    start_date: string;
    end_date: string;
  };
}

interface InstallerPerformance {
  installer_id: number;
  installer_name: string;
  total_assignments: number;
  completed_assignments: number;
  completion_rate: number;
  average_rating: number | null;
  average_duration_hours: number | null;
}

export default function PerformanceMetricsPage() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [installerPerformance, setInstallerPerformance] = useState<InstallerPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    // Set default date range (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    
    setStartDate(start.toISOString().split('T')[0]);
    setEndDate(end.toISOString().split('T')[0]);
  }, []);

  useEffect(() => {
    if (startDate && endDate) {
      loadMetrics();
    }
  }, [startDate, endDate]);

  const loadMetrics = async () => {
    try {
      setLoading(true);

      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });

      // Load overall metrics
      const metricsRes = await apiClient.get(`/crm-api/branch/metrics/?${params}`);
      setMetrics(metricsRes.data);

      // Load installer performance
      const performanceRes = await apiClient.get(`/crm-api/branch/metrics/installers/?${params}`);
      setInstallerPerformance(performanceRes.data.installers || []);
    } catch (err: any) {
      console.error('Error loading metrics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);

      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
      });

      const response = await apiClient.get(`/crm-api/branch/metrics/export/?${params}`, {
        responseType: 'blob',
      });

      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `branch_metrics_${startDate}_${endDate}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      console.error('Error exporting metrics:', err);
      alert('Failed to export metrics');
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
            <p className="mt-2 text-gray-600">Loading metrics...</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FiBarChart2 className="w-8 h-8 text-emerald-600" />
          Performance Metrics
        </h1>
        <p className="text-gray-600 mt-1">
          Track installation performance and installer productivity
        </p>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-4 mb-6">
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          <div className="flex items-center gap-2 flex-1">
            <FiCalendar className="w-5 h-5 text-gray-400" />
            <div className="flex items-center gap-2 flex-1">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
              <span className="text-gray-500">to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
          >
            <FiDownload className="w-4 h-4" />
            {exporting ? 'Exporting...' : 'Export CSV'}
          </button>
        </div>
      </div>

      {metrics && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Installations This Month</p>
                <FiCalendar className="w-5 h-5 text-emerald-500" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {metrics.kpis?.installations_this_month || 0}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Pending Installations</p>
                <FiClock className="w-5 h-5 text-yellow-500" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {metrics.kpis?.pending_installations || 0}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Completed Installations</p>
                <FiCheckCircle className="w-5 h-5 text-green-500" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {metrics.kpis?.completed_installations || 0}
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">Customer Complaints</p>
                <FiAlertCircle className="w-5 h-5 text-red-500" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {metrics.kpis?.customer_complaints || 0}
              </p>
            </div>
          </div>

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <FiTarget className="w-5 h-5 text-emerald-500" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Completion Rate
                </h3>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-emerald-600">
                  {metrics.performance?.completion_rate || 0}%
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  of installations completed
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <FiClock className="w-5 h-5 text-purple-500" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Avg Completion Time
                </h3>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-purple-600">
                  {metrics.performance?.average_completion_time_days || 0}
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  days average
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
              <div className="flex items-center gap-2 mb-4">
                <FiAward className="w-5 h-5 text-yellow-500" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Customer Satisfaction
                </h3>
              </div>
              <div className="text-center">
                <p className="text-4xl font-bold text-yellow-600">
                  {metrics.performance?.average_satisfaction_rating || 0}
                </p>
                <p className="text-sm text-gray-600 mt-2">
                  out of 5 stars
                </p>
              </div>
            </div>
          </div>

          {/* Revenue Metrics */}
          {metrics.revenue && (
            <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <FiDollarSign className="w-6 h-6 text-green-500" />
                <h3 className="text-lg font-semibold text-gray-900">
                  Revenue Summary
                </h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Revenue</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${metrics.revenue.total_revenue?.toLocaleString() || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Installation Count</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {metrics.revenue.installation_count || 0}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600 mb-1">Avg Order Value</p>
                  <p className="text-2xl font-bold text-gray-900">
                    ${metrics.revenue.average_order_value?.toLocaleString() || 0}
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* Top Performing Installers */}
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <FiUsers className="w-6 h-6 text-emerald-500" />
          <h3 className="text-lg font-semibold text-gray-900">
            Installer Performance
          </h3>
        </div>

        {installerPerformance.length === 0 ? (
          <div className="text-center py-12">
            <FiUsers className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No installer data available</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                    Installer
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Total Assignments
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Completed
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Completion Rate
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Avg Rating
                  </th>
                  <th className="text-center py-3 px-4 text-sm font-semibold text-gray-700">
                    Avg Duration
                  </th>
                </tr>
              </thead>
              <tbody>
                {installerPerformance.map((installer, index) => (
                  <tr
                    key={installer.installer_id}
                    className={`border-b border-gray-100 ${
                      index < 3 ? 'bg-emerald-50' : ''
                    }`}
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {index < 3 && (
                          <FiAward className="w-4 h-4 text-yellow-500" />
                        )}
                        <span className="font-medium text-gray-900">
                          {installer.installer_name}
                        </span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-4 text-gray-900">
                      {installer.total_assignments}
                    </td>
                    <td className="text-center py-3 px-4 text-gray-900">
                      {installer.completed_assignments}
                    </td>
                    <td className="text-center py-3 px-4">
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${
                        installer.completion_rate >= 80
                          ? 'bg-green-100 text-green-800'
                          : installer.completion_rate >= 60
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {installer.completion_rate}%
                      </span>
                    </td>
                    <td className="text-center py-3 px-4">
                      {installer.average_rating ? (
                        <div className="flex items-center justify-center gap-1">
                          <span className="text-yellow-400">★</span>
                          <span className="text-gray-900">
                            {installer.average_rating}
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="text-center py-3 px-4 text-gray-900">
                      {installer.average_duration_hours
                        ? `${installer.average_duration_hours}h`
                        : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
