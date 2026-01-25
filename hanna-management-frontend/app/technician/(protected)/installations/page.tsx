'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiTool, FiPlay, FiCheckCircle, FiClock, FiMapPin, FiCalendar } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface ChecklistProgress {
  total: number;
  completed: number;
  overall_completion: number;
}

interface InstallationRecord {
  id: string;
  customer_name?: string;
  installation_type?: string;
  installation_type_display?: string;
  installation_status?: string;
  installation_status_display?: string;
  system_size?: number;
  capacity_unit?: string;
  installation_date?: string;
  installation_address?: string;
  created_at?: string;
  has_checklists?: boolean;
  checklist_progress?: ChecklistProgress;
}

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-32"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-32"></div>
    </td>
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-16"></div>
    </td>
  </tr>
);

export default function TechnicianInstallationsPage() {
  const [records, setRecords] = useState<InstallationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();
  const router = useRouter();

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/technician/installations/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch installations. Status: ' + response.status);
      }

      const result = await response.json();
      setRecords(result.results || result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchRecords();
    }
  }, [accessToken]);

  const handleStartInstalling = (installationId: string) => {
    // Navigate to checklists page with the installation ID
    router.push(`/technician/checklists?installation=${installationId}`);
  };

  const getStatusBadgeClass = (status?: string) => {
    const statusMap: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      commissioned: 'bg-green-100 text-green-800',
      active: 'bg-green-100 text-green-800',
      decommissioned: 'bg-gray-100 text-gray-800',
    };
    return statusMap[status || ''] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'pending':
        return <FiClock className="w-4 h-4" />;
      case 'in_progress':
        return <FiTool className="w-4 h-4" />;
      case 'commissioned':
      case 'active':
        return <FiCheckCircle className="w-4 h-4" />;
      default:
        return <FiClock className="w-4 h-4" />;
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="sm:flex sm:items-center mb-6">
        <div className="sm:flex-auto">
          <div className="flex items-center">
            <FiTool className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Pending Installations</h1>
          </div>
          <p className="mt-2 text-sm text-gray-700">
            View and start installations assigned to you. Click &quot;Start Installing&quot; to begin the checklist workflow.
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md flex justify-between items-center">
          <span>Error: {error}</span>
          <button 
            onClick={fetchRecords}
            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 text-sm"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stats Cards */}
      {!loading && records.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-gray-900">
                  {records.filter(r => r.installation_status === 'pending').length}
                </p>
              </div>
              <FiClock className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">In Progress</p>
                <p className="text-2xl font-bold text-gray-900">
                  {records.filter(r => r.installation_status === 'in_progress').length}
                </p>
              </div>
              <FiTool className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Assigned</p>
                <p className="text-2xl font-bold text-gray-900">{records.length}</p>
              </div>
              <FiCheckCircle className="w-8 h-8 text-green-500" />
            </div>
          </div>
        </div>
      )}

      <div className="mt-4 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                      Customer
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Type
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Status
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Progress
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Scheduled Date
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                      Action
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
                  ) : records.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="px-6 py-10 text-center text-sm text-gray-500">
                        <FiTool className="mx-auto h-12 w-12 text-gray-400 mb-3" />
                        <p className="font-medium">No pending installations</p>
                        <p className="text-gray-400 mt-1">New installations will appear here when assigned to you.</p>
                      </td>
                    </tr>
                  ) : (
                    records.map((record) => (
                      <tr key={record.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm sm:pl-6">
                          <div className="font-medium text-gray-900">{record.customer_name || 'N/A'}</div>
                          {record.installation_address && (
                            <div className="text-xs text-gray-500 flex items-center mt-1">
                              <FiMapPin className="w-3 h-3 mr-1" />
                              <span className="truncate max-w-[200px]">{record.installation_address}</span>
                            </div>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          <span className="px-2 py-1 bg-gray-100 rounded-full text-xs font-medium">
                            {record.installation_type_display || record.installation_type?.replace('_', ' ').toUpperCase() || 'N/A'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <span className={`px-2 py-1 inline-flex items-center gap-1 text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(record.installation_status)}`}>
                            {getStatusIcon(record.installation_status)}
                            {record.installation_status_display || record.installation_status?.replace('_', ' ') || 'N/A'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          {record.has_checklists && record.checklist_progress ? (
                            <div className="w-32">
                              <div className="flex justify-between text-xs text-gray-600 mb-1">
                                <span>{record.checklist_progress.overall_completion}%</span>
                                <span>{record.checklist_progress.completed}/{record.checklist_progress.total}</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-2">
                                <div
                                  className={`h-2 rounded-full ${
                                    record.checklist_progress.overall_completion === 100 
                                      ? 'bg-green-500' 
                                      : 'bg-blue-500'
                                  }`}
                                  style={{ width: `${record.checklist_progress.overall_completion}%` }}
                                />
                              </div>
                            </div>
                          ) : (
                            <span className="text-gray-400 text-xs">No checklists</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {record.installation_date ? (
                            <div className="flex items-center">
                              <FiCalendar className="w-4 h-4 mr-1 text-gray-400" />
                              {new Date(record.installation_date).toLocaleDateString()}
                            </div>
                          ) : (
                            <span className="text-gray-400">Not scheduled</span>
                          )}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-center">
                          <button
                            onClick={() => handleStartInstalling(record.id)}
                            className={`inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                              record.installation_status === 'pending'
                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                          >
                            <FiPlay className="w-4 h-4" />
                            {record.installation_status === 'pending' ? 'Start Installing' : 'View Checklist'}
                          </button>
                        </td>
                      </tr>
                    ))
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
