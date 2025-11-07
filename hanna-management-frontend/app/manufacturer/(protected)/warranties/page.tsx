'use client';

import { useEffect, useState } from 'react';
import { FiCheckSquare } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { useEffect, useState } from 'react';
import { FiCheckSquare } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import WarrantyModal from '@/app/components/manufacturer/modals/WarrantyModal';

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
      <WarrantyModal isOpen={isModalOpen} onClose={closeModal} onSave={handleSave} warranty={selectedWarranty} />
    </main>
  );
}