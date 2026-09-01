'use client';

import { useEffect, useState } from 'react';
import { FiCheckSquare, FiPlus, FiTrash2, FiEdit, FiDownload } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import Link from 'next/link';
import { DownloadWarrantyCertificateButton } from '@/app/components/shared/DownloadButtons';
import { Alert } from '@/app/components/Alert';
import { getErrorMessage } from '@/app/hooks/useApiErrorHandler';

interface Warranty {
  id: number;
  serialized_item: number;
  customer: number;
  start_date: string;
  end_date: string;
  status: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: Warranty[];
}

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-20"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-12"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-24"></div></td>
  </tr>
);

const StatusBadge = ({ status }: { status: string }) => {
  const colors: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    expired: 'bg-red-100 text-red-800',
    void: 'bg-gray-100 text-gray-800',
  };
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

export default function WarrantiesPage() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchWarranties = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PaginatedResponse>('/crm-api/manufacturer/warranties/');
      setWarranties(response.data.results);
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarranties();
  }, []);

  const handleDelete = async (warrantyId: number) => {
    if (!confirm('Are you sure you want to delete this warranty? This action cannot be undone.')) return;
    
    setDeletingId(warrantyId);
    try {
      await apiClient.delete(`/crm-api/manufacturer/warranties/${warrantyId}/`);
      setSuccessMessage('Warranty deleted successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
      fetchWarranties();
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setDeletingId(null);
    }
  };

  const handleSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleError = (message: string) => {
    setError(message);
    setTimeout(() => setError(null), 5000);
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center">
          <FiCheckSquare className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Warranties</h1>
        </div>
        <Link 
          href="/manufacturer/warranties/new"
          className="inline-flex items-center justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition"
        >
          <FiPlus className="mr-2" />
          Create Warranty
        </Link>
      </div>

      {successMessage && (
        <Alert 
          variant="success" 
          message={successMessage} 
          onClose={() => setSuccessMessage(null)} 
          className="mb-6"
        />
      )}
      
      {error && (
        <Alert 
          variant="error" 
          message={error} 
          onClose={() => setError(null)} 
          className="mb-6"
        />
      )}

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        {loading ? (
          <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serialized Item</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Certificate</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <SkeletonRow />
                <SkeletonRow />
                <SkeletonRow />
              </tbody>
            </table>
          </div>
        ) : warranties.length === 0 ? (
          <Alert 
            variant="info" 
            message="No warranties found. Create your first warranty to get started."
          />
        ) : (
          <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serialized Item</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Certificate</th>
                  <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {warranties.map((warranty) => (
                  <tr key={warranty.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{warranty.serialized_item}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.customer}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.start_date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.end_date}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <StatusBadge status={warranty.status} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <DownloadWarrantyCertificateButton
                        warrantyId={warranty.id}
                        variant="icon"
                        size="sm"
                        isAdmin={false}
                        onSuccess={handleSuccess}
                        onError={handleError}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                      <Link 
                        href={`/manufacturer/warranties/${warranty.id}`}
                        className="inline-flex items-center text-indigo-600 hover:text-indigo-900"
                      >
                        <FiEdit className="w-4 h-4 mr-1" />
                        Edit
                      </Link>
                      <button 
                        onClick={() => handleDelete(warranty.id)} 
                        disabled={deletingId === warranty.id}
                        className="inline-flex items-center text-red-600 hover:text-red-900 disabled:opacity-50"
                      >
                        {deletingId === warranty.id ? (
                          <svg className="animate-spin h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                        ) : (
                          <FiTrash2 className="w-4 h-4 mr-1" />
                        )}
                        Delete
                      </button>
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