'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiShield } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

export default function CreateWarrantyClaimPage() {
  const [formData, setFormData] = useState({
    serial_number: '',
    description_of_fault: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();
  const router = useRouter();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/warranty/claims/create/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to create claim. Status: ${response.status}`);
      }

      router.push('/admin/warranty-claims');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiShield className="mr-3" />
          Create Warranty Claim
        </h1>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700">Serial Number</label>
              <input type="text" name="serial_number" id="serial_number" value={formData.serial_number} onChange={handleChange} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm" />
            </div>
            <div className="md:col-span-2">
              <label htmlFor="description_of_fault" className="block text-sm font-medium text-gray-700">Description of Fault</label>
              <textarea name="description_of_fault" id="description_of_fault" value={formData.description_of_fault} onChange={handleChange} rows={3} className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"></textarea>
            </div>
          </div>

          {error && <p className="mt-4 text-red-500">{error}</p>}

          <div className="mt-6">
            <button type="submit" disabled={loading} className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:bg-gray-400">
              {loading ? 'Creating...' : 'Create Claim'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
