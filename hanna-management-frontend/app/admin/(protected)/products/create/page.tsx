'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiPackage, FiArrowLeft } from 'react-icons/fi';
import Link from 'next/link';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage, normalizePaginatedResponse } from '@/app/lib/apiUtils';

interface ProductCategory {
  id: number;
  name: string;
}

import { InputField, SelectField, TextAreaField } from '@/app/components/forms/FormComponents';
import BarcodeScannerButton from '@/app/components/BarcodeScannerButton';

const PRODUCT_TYPES = [
  { value: 'hardware', label: 'Hardware Device' },
  { value: 'software', label: 'Software Package' },
  { value: 'module', label: 'Software Module' },
  { value: 'service', label: 'Professional Service' },
];

export default function CreateProductPage() {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    description: '',
    product_type: 'hardware',
    price: '',
    category: '',
    stock_quantity: '0',
    is_active: true,
    published: false,
    featured: false,
  });
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const router = useRouter();

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const response = await apiClient.get('/crm-api/products/categories/?ordering=name');
        setCategories(normalizePaginatedResponse<ProductCategory>(response.data));
      } catch (err) {
        setErrors({ api: extractErrorMessage(err, 'Failed to fetch categories') });
      }
    };
    fetchCategories();
  }, []);

  const validate = () => {
    const tempErrors: any = {};
    if (!formData.name) tempErrors.name = "Product name is required.";
    if (!formData.sku) tempErrors.sku = "SKU is required.";
    if (!formData.price) {
        tempErrors.price = "Price is required.";
    } else if (isNaN(Number(formData.price))) {
        tempErrors.price = "Price must be a number.";
    }
    if (!formData.category) tempErrors.category = "Category is required.";
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const target = e.target as HTMLInputElement;
    const { name, value, type } = target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? target.checked : value,
    }));
  };

  const handleBarcodeScanned = (barcode: string) => {
    setFormData((prev) => ({
      ...prev,
      sku: barcode,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});

    try {
      const { category, stock_quantity, ...rest } = formData;
      const res = await apiClient.post('/crm-api/products/products/', {
        ...rest,
        category_id: category ? Number(category) : null,
        stock_quantity: Number(stock_quantity) || 0,
      });

      // Go straight to the edit page so images can be added right away -
      // uploads require an existing product id.
      router.push(`/admin/products/${res.data.id}`);
    } catch (err) {
      setErrors({ api: extractErrorMessage(err, 'Failed to create product') });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiPackage className="mr-3" />
          Create Product
        </h1>
        <Link href="/admin/products" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputField id="name" label="Product Name" value={formData.name} onChange={handleChange} placeholder="e.g., Solar Panel" required error={errors.name} />
            <div className="flex items-end">
              <InputField id="sku" label="SKU" value={formData.sku} onChange={handleChange} placeholder="e.g., SP-001" required error={errors.sku} />
              <BarcodeScannerButton onScanSuccess={handleBarcodeScanned} />
            </div>
            <div className="md:col-span-2">
                <TextAreaField id="description" label="Description" value={formData.description} onChange={handleChange} placeholder="A short description of the product." />
            </div>
            <InputField id="price" label="Price" type="number" value={formData.price} onChange={handleChange} placeholder="e.g., 250.00" required error={errors.price} />
            <SelectField id="product_type" label="Product Type" value={formData.product_type} onChange={handleChange} error={errors.product_type}>
                {PRODUCT_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
            </SelectField>
            <SelectField id="category" label="Category" value={formData.category} onChange={handleChange} error={errors.category}>
                <option value="">Select a category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>{cat.name}</option>
                ))}
            </SelectField>
            <InputField id="stock_quantity" label="Stock Quantity" type="number" value={formData.stock_quantity} onChange={handleChange} placeholder="e.g., 10" />
            <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              <label htmlFor="is_active" className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" id="is_active" name="is_active" checked={formData.is_active} onChange={handleChange} className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded" />
                Active <span className="text-gray-400">(available for sale)</span>
              </label>
              <label htmlFor="published" className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" id="published" name="published" checked={formData.published} onChange={handleChange} className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded" />
                Published <span className="text-gray-400">(show on shop)</span>
              </label>
              <label htmlFor="featured" className="flex items-center gap-2 text-sm text-gray-700">
                <input type="checkbox" id="featured" name="featured" checked={formData.featured} onChange={handleChange} className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded" />
                Featured <span className="text-gray-400">(highlight on shop)</span>
              </label>
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
              ) : 'Create Product'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
