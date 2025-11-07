'use client';

import { useState, useEffect } from 'react';

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

interface WarrantyClaimModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpdateStatus: (status: string) => void;
  claim: WarrantyClaim | null;
}

export default function WarrantyClaimModal({ isOpen, onClose, onUpdateStatus, claim }: WarrantyClaimModalProps) {
  const [newStatus, setNewStatus] = useState('');

  useEffect(() => {
    if (claim) {
      setNewStatus(claim.status);
    }
  }, [claim]);

  if (!isOpen || !claim) return null;

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setNewStatus(e.target.value);
  };

  const handleUpdate = () => {
    onUpdateStatus(newStatus);
  };

  return (
    <div className="fixed z-10 inset-0 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
        </div>
        <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Warranty Claim Details</h3>
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
          </div>
          <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button onClick={handleUpdate} type="button" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm">
              Update Status
            </button>
            <button onClick={onClose} type="button" className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
