'use client';

import { useState } from 'react';
import { FiPlus, FiCheck, FiAlertCircle } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

export default function AddSerialPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [formData, setFormData] = useState({
    product_id: '',
    serial_number: '',
    barcode: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const response = await apiClient.post('/crm-api/products/retailer-branch/add-serial-number/', {
        product_id: parseInt(formData.product_id, 10),
        serial_number: formData.serial_number,
        barcode: formData.barcode || undefined,
      });
      setResult({ success: true, message: response.data.message || 'Serial number added successfully!' });
      setFormData({ product_id: '', serial_number: '', barcode: '' });
    } catch (err: any) {
      setResult({ 
        success: false, 
        message: err.response?.data?.error || err.message || 'Failed to add serial number.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">Add Serial Number</h1>
      
      {/* Result Message */}
      {result && (
        <div className={`mb-6 p-4 rounded-lg flex items-center ${
          result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          {result.success ? (
            <FiCheck className="text-green-600 mr-3 h-5 w-5" />
          ) : (
            <FiAlertCircle className="text-red-600 mr-3 h-5 w-5" />
          )}
          <span className={result.success ? 'text-green-800' : 'text-red-800'}>
            {result.message}
          </span>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md border p-6 max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex items-center mb-4">
            <FiPlus className="h-6 w-6 text-emerald-600 mr-2" />
            <h2 className="text-xl font-semibold text-gray-800">Register New Serialized Item</h2>
          </div>
          <p className="text-gray-600 mb-6">
            Add a new serialized item to your inventory by entering the product ID and serial number.
          </p>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product ID *</label>
            <input
              type="number"
              required
              value={formData.product_id}
              onChange={(e) => setFormData({ ...formData, product_id: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="Enter product ID"
            />
            <p className="mt-1 text-sm text-gray-500">
              The numeric ID of the product from the products list.
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Serial Number *</label>
            <input
              type="text"
              required
              value={formData.serial_number}
              onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="e.g., SN12345678"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Barcode (Optional)</label>
            <input
              type="text"
              value={formData.barcode}
              onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="e.g., 1234567890123"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Adding...' : 'Add Serial Number'}
          </button>
        </form>
      </div>
    </main>
  );
}
