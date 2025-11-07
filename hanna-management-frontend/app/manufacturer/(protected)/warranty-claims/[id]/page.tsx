'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { WarrantyClaim } from '@/app/types';

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
    try {
      await apiClient.patch(`/crm-api/manufacturer/warranty-claims/${id}/`, { status: newStatus });
      router.push('/manufacturer/warranty-claims');
    } catch (err: any) {
      setError(err.message || 'Failed to update warranty claim.');
    }
  };

  if (loading) {
    return <p className="text-center text-gray-500 py-4">Loading...</p>;
  }

  if (error) {
    return <p className="text-center text-red-500 py-4">Error: {error}</p>;
  }

  if (!claim) {
    return <p className="text-center text-gray-500 py-4">No claim found.</p>;
  }

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Warranty Claim Details</h1>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="mt-2">
          <p className="text-sm text-gray-500"><strong>Claim ID:</strong> {claim.claim_id}</p>
          <p className="text-sm text-gray-500"><strong>Product:</strong> {claim.product_name} (SN: {claim.product_serial_number})</p>
          <p className="text-sm text-gray-500"><strong>Customer:</strong> {claim.customer_name}</p>
          <p className="text-sm text-gray-500"><strong>Current Status:</strong> {claim.status}</p>
          <p className="text-sm text-gray-500"><strong>Date:</strong> {new Date(claim.created_at).toLocaleDateString()}</p>
          <div className="mt-4">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700">Update Status</label>
            <select
              id="status"
              name="status"
              className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              value={newStatus}
              onChange={handleStatusChange}
            >
              <option value="pending">Pending Review</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="closed">Closed</option>
            </select>
          </div>
        </div>
        <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
          <button onClick={handleUpdate} type="button" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm">
            Update Status
          </button>
          <button onClick={() => router.push('/manufacturer/warranty-claims')} type="button" className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
            Back
          </button>
        </div>
      </div>
    </main>
  );
}
