'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/app/store/authStore';
import { FiArrowLeft, FiSave } from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';

interface ProductCategory {
  id: number;
  name: string;
  description: string;
}

export default function EditProductCategoryPage({ params }: { params: Promise<{ id: string }> }) {
  const [category, setCategory] = useState<ProductCategory | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
  });
  const { accessToken } = useAuthStore();
  const router = useRouter();
  const [categoryId, setCategoryId] = useState<string>('');

  useEffect(() => {
    params.then((p) => setCategoryId(p.id));
  }, [params]);

  useEffect(() => {
    const fetchCategory = async () => {
      if (!categoryId || !accessToken) return;

      try {
        const response = await apiClient.get(`/crm-api/products/categories/${categoryId}/`);
        const data = response.data;
        setCategory(data);
        setFormData({
          name: data.name || '',
          description: data.description || '',
        });
      } catch (err: unknown) {
        setError(extractErrorMessage(err, 'Failed to fetch category.'));
      } finally {
        setLoading(false);
      }
    };

    if (categoryId && accessToken) {
      fetchCategory();
    }
  }, [categoryId, accessToken]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      await apiClient.put(`/crm-api/products/categories/${categoryId}/`, formData);
      router.push('/admin/product-categories');
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to update category.'));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (error && !category) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-red-500">Error: {error}</p>
      </div>
    );
  }

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          Edit Product Category
        </h1>
        <Link href="/admin/product-categories">
          <span className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to Categories
          </span>
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Category Name *
            </label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={4}
              className="w-full px-4 py-3 bg-white border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300"
            />
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Link href="/admin/product-categories">
              <span className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition">
                Cancel
              </span>
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FiSave className="mr-2" />
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
