'use client';

import { useEffect, useState } from 'react';
import { FiTool } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import { DownloadInstallationReportButton } from '@/app/components/shared/DownloadButtons';

interface InstallationSystemRecord {
  id: string;
  customer_name?: string;
  installation_type?: string;
  installation_status?: string;
  system_size?: number;
  capacity_unit?: string;
  installation_date?: string;
  commissioning_date?: string;
  installation_address?: string;
  created_at?: string;
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
  const [records, setRecords] = useState<InstallationSystemRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  const fetchRecords = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/technician/installations/`, {
        headers: {
          'Authorization': `******
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch installations. Status: ${response.status}`);
      }

      const result = await response.json();
      setRecords(result.results || result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchRecords();
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
      pending: 'bg-yellow-100 text-yellow-800',
      in_progress: 'bg-blue-100 text-blue-800',
      commissioned: 'bg-green-100 text-green-800',
      active: 'bg-green-100 text-green-800',
      decommissioned: 'bg-gray-100 text-gray-800',
    };
    return statusMap[status || ''] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="sm:flex sm:items-center mb-6">
        <div className="sm:flex-auto">
          <div className="flex items-center">
            <FiTool className="h-8 w-8 text-gray-700 mr-3" />
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">My Installations</h1>
          </div>
          <p className="mt-2 text-sm text-gray-700">
            View and download reports for installations you have completed.
          </p>
        </div>
      </div>

      {successMessage && (
        <div className="mb-4 p-4 bg-green-100 text-green-700 rounded-md">
          {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          {errorMessage}
        </div>
      )}
      {error && (
        <div className="mb-4 p-4 bg-red-100 text-red-700 rounded-md">
          Error: {error}
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
                      System Size
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                      Installation Date
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-center text-sm font-semibold text-gray-900">
                      Report
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
                        No installations found. Completed installations will appear here.
                      </td>
                    </tr>
                  ) : (
                    records.map((record) => (
                      <tr key={record.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                          {record.customer_name || 'N/A'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {record.installation_type?.replace('_', ' ').toUpperCase() || 'N/A'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusBadgeClass(record.installation_status)}`}>
                            {record.installation_status?.replace('_', ' ') || 'N/A'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {record.system_size ? `${record.system_size} ${record.capacity_unit || ''}` : 'N/A'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {record.installation_date ? new Date(record.installation_date).toLocaleDateString() : 'N/A'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-center">
                          <DownloadInstallationReportButton
                            installationId={record.id}
                            variant="icon"
                            size="sm"
                            isAdmin={false}
                            onSuccess={handleSuccess}
                            onError={handleError}
                          />
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
