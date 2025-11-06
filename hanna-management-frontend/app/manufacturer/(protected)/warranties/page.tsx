'use client';

import { useEffect, useState } from 'react';
import { FiCheckSquare } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

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

export default function WarrantiesPage() {
  const [warranties, setWarranties] = useState<Warranty[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedWarranty, setSelectedWarranty] = useState<Warranty | null>(null);

  const fetchWarranties = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<PaginatedResponse>('/crm-api/manufacturer/warranties/');
      setWarranties(response.data.results);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch warranties.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarranties();
  }, []);

  const openModal = (warranty: Warranty | null) => {
    setSelectedWarranty(warranty);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setSelectedWarranty(null);
    setIsModalOpen(false);
  };

  const handleSave = async (warrantyData: Partial<Warranty>) => {
    try {
      if (selectedWarranty) {
        await apiClient.put(`/crm-api/manufacturer/warranties/${selectedWarranty.id}/`, warrantyData);
      } else {
        await apiClient.post('/crm-api/manufacturer/warranties/', warrantyData);
      }
      fetchWarranties();
      closeModal();
    } catch (err: any) {
      setError(err.message || 'Failed to save warranty.');
    }
  };

  const handleDelete = async (warrantyId: number) => {
    try {
      await apiClient.delete(`/crm-api/manufacturer/warranties/${warrantyId}/`);
      fetchWarranties();
    } catch (err: any) {
      setError(err.message || 'Failed to delete warranty.');
    }
  };

  useEffect(() => {
    const fetchWarranties = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<PaginatedResponse>('/crm-api/manufacturer/warranties/');
        setWarranties(response.data.results);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch warranties.');
      } finally {
        setLoading(false);
      }
    };

    fetchWarranties();
  }, []);

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <FiCheckSquare className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Warranties</h1>
        </div>
        <button onClick={() => openModal(null)} className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
          Create Warranty
        </button>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        {loading && <p className="text-center text-gray-500 py-4">Loading warranties...</p>}
        {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
        {!loading && !error && (
          <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serialized Item</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">End Date</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {warranties.map((warranty) => (
                  <tr key={warranty.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{warranty.serialized_item}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.customer}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.start_date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.end_date}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{warranty.status}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button onClick={() => openModal(warranty)} className="text-indigo-600 hover:text-indigo-900">Edit</button>
                      <button onClick={() => handleDelete(warranty.id)} className="text-red-600 hover:text-red-900 ml-4">Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      {isModalOpen && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 transition-opacity" aria-hidden="true">
              <div className="absolute inset-0 bg-gray-500 opacity-75"></div>
            </div>
            <span className="hidden sm:inline-block sm:align-middle sm:h-screen" aria-hidden="true">&#8203;</span>
            <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
              <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">{selectedWarranty ? 'Edit Warranty' : 'Create Warranty'}</h3>
                <div className="mt-2">
                  <form onSubmit={(e) => {
                    e.preventDefault();
                    const formData = new FormData(e.currentTarget);
                    const data = Object.fromEntries(formData.entries());
                    handleSave(data);
                  }}>
                    <div className="mb-4">
                      <label htmlFor="serialized_item" className="block text-sm font-medium text-gray-700">Serialized Item</label>
                      <input type="text" name="serialized_item" id="serialized_item" defaultValue={selectedWarranty?.serialized_item} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                    </div>
                    <div className="mb-4">
                      <label htmlFor="customer" className="block text-sm font-medium text-gray-700">Customer</label>
                      <input type="text" name="customer" id="customer" defaultValue={selectedWarranty?.customer} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                    </div>
                    <div className="mb-4">
                      <label htmlFor="start_date" className="block text-sm font-medium text-gray-700">Start Date</label>
                      <input type="date" name="start_date" id="start_date" defaultValue={selectedWarranty?.start_date} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                    </div>
                    <div className="mb-4">
                      <label htmlFor="end_date" className="block text-sm font-medium text-gray-700">End Date</label>
                      <input type="date" name="end_date" id="end_date" defaultValue={selectedWarranty?.end_date} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                    </div>
                    <div className="mb-4">
                      <label htmlFor="status" className="block text-sm font-medium text-gray-700">Status</label>
                      <input type="text" name="status" id="status" defaultValue={selectedWarranty?.status} className="mt-1 focus:ring-indigo-500 focus:border-indigo-500 block w-full shadow-sm sm:text-sm border-gray-300 rounded-md" />
                    </div>
                    <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                      <button type="submit" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm">
                        Save
                      </button>
                      <button onClick={closeModal} type="button" className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              </div>
              <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
                <button type="button" className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm">
                  Save
                </button>
                <button onClick={closeModal} type="button" className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
