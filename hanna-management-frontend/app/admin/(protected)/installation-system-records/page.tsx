'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiTool, FiFilter } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import ActionButtons from '@/app/components/shared/ActionButtons';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';
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

const INSTALLATION_STATUSES = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'commissioned', label: 'Commissioned' },
  { value: 'active', label: 'Active' },
  { value: 'decommissioned', label: 'Decommissioned' },
];

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
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
    <td className="px-6 py-4 whitespace-nowrap">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
  </tr>
);

export default function InstallationSystemRecordsPage() {
  const [records, setRecords] = useState<InstallationSystemRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [recordToDelete, setRecordToDelete] = useState<InstallationSystemRecord | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [updatingStatusId, setUpdatingStatusId] = useState<string | null>(null);
  const { accessToken } = useAuthStore();
  const router = useRouter();

  const fetchRecords = async (statusFilterValue?: string) => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const filterParam = statusFilterValue ? `?installation_status=${statusFilterValue}` : '';
      const response = await fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/${filterParam}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch data. Status: ${response.status}`);
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
      fetchRecords(statusFilter);
    }
  }, [accessToken, statusFilter]);
  
  const handleStatusChange = async (recordId: string, newStatus: string) => {
    setUpdatingStatusId(recordId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/${recordId}/update_status/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (!response.ok) {
        throw new Error('Failed to update status');
      }

      // Update local state
      setRecords(prev => 
        prev.map(record => 
          record.id === recordId 
            ? { ...record, installation_status: newStatus }
            : record
        )
      );
      handleSuccess('Status updated successfully');
    } catch (err: any) {
      handleError(err.message || 'Failed to update status');
    } finally {
      setUpdatingStatusId(null);
    }
  };

  const handleDeleteClick = (record: InstallationSystemRecord) => {
    setRecordToDelete(record);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!recordToDelete || !recordToDelete.id) return;

    setIsDeleting(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/admin-panel/installation-system-records/${recordToDelete.id}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });

      if (!response.ok) throw new Error('Delete failed');

      setDeleteModalOpen(false);
      setRecordToDelete(null);
      fetchRecords(statusFilter);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setRecordToDelete(null);
  };

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
      <div className="sm:flex sm:items-center sm:justify-between mb-6">
        <div className="sm:flex-auto">
          <div className="flex items-center">
            <FiTool className="h-8 w-8 text-gray-700 mr-3" />
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Installation System Records</h1>
          </div>
          <p className="mt-2 text-sm text-gray-700">
            A comprehensive list of all system installation records with commissioning details.
          </p>
        </div>
        <div className="mt-4 sm:mt-0 sm:ml-16 sm:flex-none">
          <button
            type="button"
            onClick={() => router.push('/admin/installation-system-records/create')}
            className="inline-flex items-center justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 sm:w-auto"
          >
            Create New Record
          </button>
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

      {/* Status Filter */}
      <div className="mb-4 flex items-center gap-2">
        <FiFilter className="text-gray-500" />
        <label htmlFor="statusFilter" className="text-sm font-medium text-gray-700">
          Filter by Status:
        </label>
        <select
          id="statusFilter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          {INSTALLATION_STATUSES.map(status => (
            <option key={status.value} value={status.value}>{status.label}</option>
          ))}
        </select>
        {statusFilter && (
          <button
            type="button"
            onClick={() => setStatusFilter('')}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear filter
          </button>
        )}
      </div>

      <div className="mt-4 flow-root">
        <div className="-mx-4 -my-2 overflow-x-auto sm:-mx-6 lg:-mx-8">
          <div className="inline-block min-w-full py-2 align-middle sm:px-6 lg:px-8">
            <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
              <table className="min-w-full divide-y divide-gray-300">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                      ID
                    </th>
                    <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
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
                    <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                      <span className="sr-only">Actions</span>
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
                      <td colSpan={8} className="px-6 py-10 text-center text-sm text-gray-500">
                        No installation system records found.
                      </td>
                    </tr>
                  ) : (
                    records.map((record) => (
                      <tr key={record.id} className="hover:bg-gray-50">
                        <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                          {record.id?.slice(0, 8)}...
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {record.customer_name || 'N/A'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                          {record.installation_type?.replace('_', ' ').toUpperCase() || 'N/A'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-4 text-sm">
                          <select
                            value={record.installation_status || ''}
                            onChange={(e) => handleStatusChange(record.id, e.target.value)}
                            disabled={updatingStatusId === record.id}
                            className={`text-xs font-semibold rounded-full px-2 py-1 border-0 cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 ${getStatusBadgeClass(record.installation_status)} ${updatingStatusId === record.id ? 'opacity-50 cursor-wait' : ''}`}
                          >
                            {INSTALLATION_STATUSES.map(status => (
                              <option key={status.value} value={status.value}>{status.label}</option>
                            ))}
                          </select>
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
                            isAdmin={true}
                            onSuccess={handleSuccess}
                            onError={handleError}
                          />
                        </td>
                        <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                          <ActionButtons
                            entityId={record.id}
                            showView={true}
                            viewPath={`/admin/installation-system-records/${record.id}`}
                            showEdit={true}
                            editPath={`/admin/installation-system-records/${record.id}/edit`}
                            onDelete={() => handleDeleteClick(record)}
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

      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        isDeleting={isDeleting}
        title="Delete Installation Record"
        message={`Are you sure you want to delete Installation System Record ${recordToDelete?.id?.slice(0, 8)}? This action cannot be undone.`}
      />
    </div>
  );
}
