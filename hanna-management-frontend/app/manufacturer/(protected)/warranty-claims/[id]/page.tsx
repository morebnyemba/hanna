'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { WarrantyClaim } from '@/app/types';
import { FiShield, FiArrowLeft } from 'react-icons/fi';
import Link from 'next/link';

const SelectField = ({ id, label, value, onChange, children, error }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void; children: React.ReactNode; error?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <select
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            className={`mt-1 block w-full px-4 py-3 bg-white border ${error ? 'border-red-500' : 'border-gray-300'} rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300`}
        >
            {children}
        </select>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
);

const SkeletonLoader = () => (
    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200 animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-3/4 mb-6"></div>
        <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="mt-6">
            <div className="h-10 bg-gray-200 rounded w-full"></div>
        </div>
        <div className="mt-6 flex justify-end space-x-4">
            <div className="h-10 w-24 bg-gray-200 rounded"></div>
            <div className="h-10 w-24 bg-gray-200 rounded"></div>
        </div>
    </div>
);

export default function EditWarrantyClaimPage() {
  const router = useRouter();
  const params = useParams();
  const { id } = params;

  const [claim, setClaim] = useState<WarrantyClaim | null>(null);
  const [newStatus, setNewStatus] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      apiClient.get(`/crm-api/manufacturer/warranty-claims/${id}/`)
        .then(response => {
          setClaim(response.data);
          setNewStatus(response.data.status);
          setLoading(false);
        })
        .catch(err => {
          setError(err.message || 'Failed to fetch warranty claim data.');
          setLoading(false);
        });
    }
  }, [id]);

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setNewStatus(e.target.value);
  };

  const handleUpdate = async () => {
    setError(null);
    setLoading(true);
    try {
      await apiClient.patch(`/crm-api/manufacturer/warranty-claims/${id}/`, { status: newStatus });
      router.push('/manufacturer/warranty-claims');
    } catch (err: any) {
      setError(err.message || 'Failed to update warranty claim.');
    } finally {
        setLoading(false);
    }
  };

  if (loading) {
    return <SkeletonLoader />;
  }

  if (error) {
    return <p className="text-center text-red-500 py-4">Error: {error}</p>;
  }

  if (!claim) {
    return <p className="text-center text-gray-500 py-4">No claim found.</p>;
  }

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
            <FiShield className="mr-3" />
            Warranty Claim Details
        </h1>
        <Link href="/manufacturer/warranty-claims" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="md:col-span-2 space-y-2">
                <p className="text-sm text-gray-500"><strong>Claim ID:</strong> {claim.claim_id}</p>
                <p className="text-sm text-gray-500"><strong>Product:</strong> {claim.product_name} (SN: {claim.product_serial_number})</p>
                <p className="text-sm text-gray-500"><strong>Customer:</strong> {claim.customer_name}</p>
                <p className="text-sm text-gray-500"><strong>Current Status:</strong> {claim.status}</p>
                <p className="text-sm text-gray-500"><strong>Date:</strong> {new Date(claim.created_at).toLocaleDateString()}</p>
            </div>
            <div className="md:col-span-2">
                <SelectField id="status" label="Update Status" value={newStatus} onChange={handleStatusChange}>
                    <option value="pending">Pending Review</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                    <option value="in_progress">In Progress</option>
                    <option value="completed">Completed</option>
                    <option value="closed">Closed</option>
                </SelectField>
            </div>
        </div>
        <div className="mt-6 flex justify-end">
            <button onClick={handleUpdate} type="button" disabled={loading} className="w-full sm:w-auto flex justify-center py-3 px-6 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02]">
              {loading ? 'Updating...' : 'Update Status'}
            </button>
          </div>
      </div>
    </main>
  );
}