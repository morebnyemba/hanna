'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FiBox, FiPlus, FiTrash2, FiSearch } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Alert } from '@/app/components/Alert';
import { getErrorMessage } from '@/app/hooks/useApiErrorHandler';

interface SerializedItem {
  id: number;
  serial_number: string;
  product: {
    id: number;
    name: string;
    sku: string;
    product_type: string;
    price: number;
  };
  created_at: string;
}

const productTypeColors: Record<string, string> = {
  hardware: 'bg-blue-100 text-blue-800',
  software: 'bg-purple-100 text-purple-800',
  service: 'bg-green-100 text-green-800',
  module: 'bg-orange-100 text-orange-800',
};

export default function SerializedItemsPage() {
  const [items, setItems] = useState<SerializedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [deleteLoading, setDeleteLoading] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchSerializedItems();
  }, []);

  const fetchSerializedItems = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/crm-api/manufacturer/serialized-items/');
      // Handle both paginated response (with results) and plain array
      const data = response.data;
      if (Array.isArray(data)) {
        setItems(data);
      } else if (data.results && Array.isArray(data.results)) {
        setItems(data.results);
      } else {
        setItems([]);
      }
    } catch (err) {
      console.error('Failed to fetch serialized items:', err);
      setError('Failed to load serialized items. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this serialized item?')) return;

    setDeleteLoading(id);
    setError(null);
    try {
      await apiClient.delete(`/crm-api/manufacturer/serialized-items/${id}/`);
      setItems((prev) => prev.filter((item) => item.id !== id));
      setSuccessMessage('Serialized item deleted successfully');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to delete serialized item:', err);
      setError(getErrorMessage(err));
    } finally {
      setDeleteLoading(null);
    }
  };

  const filteredItems = items.filter(
    (item) =>
      item.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.product.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiBox className="mr-3" />
          Serialized Items
        </h1>
        <Link
          href="/manufacturer/serialized-items/new"
          className="w-full sm:w-auto flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition"
        >
          <FiPlus className="mr-2" />
          Add New Item
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

      {/* Search Bar */}
      <div className="mb-6 relative">
        <FiSearch className="absolute left-3 top-3 text-gray-400" />
        <input
          type="text"
          placeholder="Search by serial number or product name..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        </div>
      )}

      {/* Items Table */}
      {!loading && (
        <>
          {filteredItems.length === 0 ? (
            <div className="bg-white p-8 rounded-lg shadow-md border border-gray-200 text-center">
              <FiBox className="mx-auto mb-4 h-12 w-12 text-gray-400" />
              <p className="text-gray-600 mb-4">
                {items.length === 0
                  ? 'No serialized items yet. Start by adding your first item.'
                  : 'No items match your search criteria.'}
              </p>
              {items.length === 0 && (
                <Link
                  href="/manufacturer/serialized-items/new"
                  className="inline-flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition"
                >
                  <FiPlus className="mr-2" />
                  Add First Item
                </Link>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Serial Number
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Price
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Added
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {filteredItems.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="font-mono text-sm font-semibold text-gray-900">
                            {item.serial_number}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900 font-medium">{item.product.name}</div>
                          <div className="text-xs text-gray-500">{item.product.sku || 'No SKU'}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span
                            className={`px-3 py-1 text-xs font-medium rounded-full ${
                              productTypeColors[item.product.product_type] ||
                              'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {item.product.product_type.charAt(0).toUpperCase() +
                              item.product.product_type.slice(1)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="text-sm font-medium text-gray-900">
                            ${parseFloat(item.product.price?.toString() || '0').toFixed(2)}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {new Date(item.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right">
                          <button
                            onClick={() => handleDelete(item.id)}
                            disabled={deleteLoading === item.id}
                            className="inline-flex items-center px-3 py-1 text-red-600 hover:text-red-900 hover:bg-red-50 rounded-md transition disabled:opacity-50"
                          >
                            {deleteLoading === item.id ? (
                              <svg
                                className="animate-spin h-4 w-4"
                                xmlns="http://www.w3.org/2000/svg"
                                fill="none"
                                viewBox="0 0 24 24"
                              >
                                <circle
                                  className="opacity-25"
                                  cx="12"
                                  cy="12"
                                  r="10"
                                  stroke="currentColor"
                                  strokeWidth="4"
                                ></circle>
                                <path
                                  className="opacity-75"
                                  fill="currentColor"
                                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                                ></path>
                              </svg>
                            ) : (
                              <FiTrash2 className="h-4 w-4" />
                            )}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Summary */}
          {filteredItems.length > 0 && (
            <div className="mt-4 text-sm text-gray-600">
              Showing {filteredItems.length} of {items.length} item(s)
            </div>
          )}
        </>
      )}
    </main>
  );
}
