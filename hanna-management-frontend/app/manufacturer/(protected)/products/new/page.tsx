'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { Product } from '@/app/types';
import { InputField, SelectField, TextAreaField } from './FormComponents';
import { FiPackage, FiArrowLeft } from 'react-icons/fi';
import Link from 'next/link';

const productTypes = ["Solar Panel", "Inverter", "Battery", "Other"];

export default function NewProductPage() {
  const router = useRouter();
  const [formData, setFormData] = useState<Partial<Product>>({
    name: '',
    sku: '',
    price: '',
    product_type: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});

  const validate = () => {
    const tempErrors: any = {};
    if (!formData.name) tempErrors.name = "Product name is required.";
    if (!formData.sku) tempErrors.sku = "SKU is required.";
    if (!formData.price) {
        tempErrors.price = "Price is required.";
    } else if (isNaN(Number(formData.price))) {
        tempErrors.price = "Price must be a number.";
    }
    if (!formData.product_type) tempErrors.product_type = "Product type is required.";
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});
    try {
      await apiClient.post('/crm-api/manufacturer/products/', formData);
      router.push('/manufacturer/products');
    } catch (err: any) {
      setErrors({ api: err.message || 'Failed to create product.' });
    } finally {
        setLoading(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
            <FiPackage className="mr-3" />
            Create Product
        </h1>
        <Link href="/manufacturer/products" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputField id="name" label="Product Name" value={formData.name || ''} onChange={handleInputChange} placeholder="e.g., Solar Panel" required error={errors.name} />
            <InputField id="sku" label="SKU" value={formData.sku || ''} onChange={handleInputChange} placeholder="e.g., SP-001" required error={errors.sku} />
            <InputField id="price" label="Price" type="number" value={formData.price || ''} onChange={handleInputChange} placeholder="e.g., 250.00" required error={errors.price} />
            <SelectField id="product_type" label="Product Type" value={formData.product_type || ''} onChange={handleInputChange} error={errors.product_type}>
                <option value="">Select a product type</option>
                {productTypes.map(type => <option key={type} value={type}>{type}</option>)}
            </SelectField>
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
              ) : 'Create Product'}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}