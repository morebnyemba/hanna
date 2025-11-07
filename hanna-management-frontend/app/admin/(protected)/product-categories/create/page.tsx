'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiList, FiArrowLeft } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';

interface ProductCategory {
  id: number;
  name: string;
}

const InputField = ({ id, label, value, onChange, required = false, type = 'text', placeholder = '', error }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLInputElement>) => void; required?: boolean; type?: string; placeholder?: string; error?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <input
            type={type}
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            required={required}
            placeholder={placeholder}
            className={`mt-1 block w-full px-4 py-3 bg-white border ${error ? 'border-red-500' : 'border-gray-300'} rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300`}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
);

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

const TextAreaField = ({ id, label, value, onChange, required = false, placeholder = '' }: { id: string; label: string; value: string; onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void; required?: boolean; placeholder?: string; }) => (
    <div>
        <label htmlFor={id} className="block text-sm font-medium text-gray-700">{label}</label>
        <textarea
            id={id}
            name={id}
            value={value}
            onChange={onChange}
            required={required}
            placeholder={placeholder}
            rows={3}
            className="mt-1 block w-full px-4 py-3 bg-white border border-gray-300 rounded-xl shadow-sm focus:outline-none focus:ring-purple-500 focus:border-purple-500 sm:text-sm transition-all duration-300"
        />
    </div>
);

export default function CreateProductCategoryPage() {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    parent: '',
  });
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/products/categories/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch categories');
        }
        const data = await response.json();
        setCategories(data.results);
      } catch (err: any) {
        setErrors({ api: err.message });
      }
    };
    if (accessToken) {
      fetchCategories();
    }
  }, [accessToken]);

  const validate = () => {
    let tempErrors: any = {};
    if (!formData.name) tempErrors.name = "Category name is required.";
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/products/categories/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Failed to create category. Status: ${response.status}`);
      }

      router.push('/admin/product-categories');
    } catch (err: any) {
      setErrors({ api: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiList className="mr-3" />
          Create Product Category
        </h1>
        <Link href="/admin/product-categories" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputField id="name" label="Category Name" value={formData.name} onChange={handleChange} placeholder="e.g., Solar Panels" required error={errors.name} />
            <SelectField id="parent" label="Parent Category" value={formData.parent} onChange={handleChange}>
                <option value="">Select a parent category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
            </SelectField>
            <div className="md:col-span-2">
                <TextAreaField id="description" label="Description" value={formData.description} onChange={handleChange} placeholder="A short description of the product category." />
            </div>
          </div>

          {errors.api && (
            <div className="mt-4 rounded-xl bg-red-500/20 p-4 border border-red-500/30">
                <div className="flex">
                <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </div>
                <div className="ml-3">
                    <p className="text-sm text-red-400">{errors.api}</p>
                </div>
                </div>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button type="submit" disabled={loading} className="w-full sm:w-auto flex justify-center py-3 px-6 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02]">
              {loading ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating...
                  </>
              ) : 'Create Category'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
