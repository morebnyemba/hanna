'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/lib/apiClient';
import { FiArrowLeft, FiBox } from 'react-icons/fi';
import Link from 'next/link';

interface Product {
  id: number;
  name: string;
  sku: string;
  product_type: string;
  price: number;
}

const productTypes = [
  { label: "Software Package", value: "software" },
  { label: "Professional Service", value: "service" },
  { label: "Hardware Device", value: "hardware" },
  { label: "Software Module", value: "module" },
];

export default function AddSerializedItemPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const [useExisting, setUseExisting] = useState(true);
  
  const [formData, setFormData] = useState({
    serial_number: '',
    product_id: '',
    product_name: '',
    product_type: 'hardware',
    sku: '',
    price: '',
    description: '',
  });

  useEffect(() => {
    // Fetch existing products
    const fetchProducts = async () => {
      try {
        const response = await apiClient.get<{ results: Product[] }>('/crm-api/manufacturer/products/');
        setProducts(response.data.results || []);
      } catch (err) {
        console.error('Failed to fetch products:', err);
      }
    };
    fetchProducts();
  }, []);

  const validate = () => {
    const tempErrors: any = {};
    if (!formData.serial_number) {
      tempErrors.serial_number = "Serial number is required.";
    }

    if (useExisting) {
      if (!formData.product_id) {
        tempErrors.product_id = "Please select a product.";
      }
    } else {
      if (!formData.product_name) {
        tempErrors.product_name = "Product name is required.";
      }
      if (!formData.product_type) {
        tempErrors.product_type = "Product type is required.";
      }
    }

    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setErrors({});

    try {
      const payload: any = {
        serial_number: formData.serial_number,
      };

      if (useExisting) {
        payload.product_id = parseInt(formData.product_id);
      } else {
        payload.product_name = formData.product_name;
        payload.product_type = formData.product_type;
        if (formData.sku) payload.sku = formData.sku;
        if (formData.price) payload.price = parseFloat(formData.price);
        if (formData.description) payload.description = formData.description;
      }

      await apiClient.post('/crm-api/manufacturer/serialized-items/', payload);
      router.push('/manufacturer/serialized-items');
    } catch (err: any) {
      setErrors({ api: err.message || 'Failed to create serialized item.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiBox className="mr-3" />
          Add Serialized Item
        </h1>
        <Link
          href="/manufacturer/serialized-items"
          className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition"
        >
          <FiArrowLeft className="mr-2" />
          Back
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          {/* Serial Number */}
          <div className="mb-6">
            <label htmlFor="serial_number" className="block text-sm font-medium text-gray-700 mb-2">
              Serial Number *
            </label>
            <input
              id="serial_number"
              name="serial_number"
              type="text"
              value={formData.serial_number}
              onChange={handleInputChange}
              placeholder="e.g., SN-12345"
              className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                errors.serial_number ? 'border-red-500' : 'border-gray-300'
              }`}
              required
            />
            {errors.serial_number && (
              <p className="text-red-500 text-sm mt-1">{errors.serial_number}</p>
            )}
          </div>

          {/* Toggle between existing and new product */}
          <div className="mb-6 p-4 bg-gray-50 rounded-md">
            <div className="flex items-center gap-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="productMode"
                  checked={useExisting}
                  onChange={() => setUseExisting(true)}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Use Existing Product</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  name="productMode"
                  checked={!useExisting}
                  onChange={() => setUseExisting(false)}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Create New Product</span>
              </label>
            </div>
          </div>

          {/* Existing Product Selection */}
          {useExisting && (
            <div className="mb-6">
              <label htmlFor="product_id" className="block text-sm font-medium text-gray-700 mb-2">
                Select Product *
              </label>
              <select
                id="product_id"
                name="product_id"
                value={formData.product_id}
                onChange={handleInputChange}
                className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                  errors.product_id ? 'border-red-500' : 'border-gray-300'
                }`}
                required={useExisting}
              >
                <option value="">Select a product</option>
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.name} ({product.sku || 'No SKU'})
                  </option>
                ))}
              </select>
              {errors.product_id && (
                <p className="text-red-500 text-sm mt-1">{errors.product_id}</p>
              )}
            </div>
          )}

          {/* New Product Creation */}
          {!useExisting && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Product Name */}
                <div>
                  <label htmlFor="product_name" className="block text-sm font-medium text-gray-700 mb-2">
                    Product Name *
                  </label>
                  <input
                    id="product_name"
                    name="product_name"
                    type="text"
                    value={formData.product_name}
                    onChange={handleInputChange}
                    placeholder="e.g., Solar Panel"
                    className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                      errors.product_name ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required={!useExisting}
                  />
                  {errors.product_name && (
                    <p className="text-red-500 text-sm mt-1">{errors.product_name}</p>
                  )}
                </div>

                {/* Product Type */}
                <div>
                  <label htmlFor="product_type" className="block text-sm font-medium text-gray-700 mb-2">
                    Product Type *
                  </label>
                  <select
                    id="product_type"
                    name="product_type"
                    value={formData.product_type}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 ${
                      errors.product_type ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required={!useExisting}
                  >
                    {productTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                  {errors.product_type && (
                    <p className="text-red-500 text-sm mt-1">{errors.product_type}</p>
                  )}
                </div>

                {/* SKU */}
                <div>
                  <label htmlFor="sku" className="block text-sm font-medium text-gray-700 mb-2">
                    SKU (Optional)
                  </label>
                  <input
                    id="sku"
                    name="sku"
                    type="text"
                    value={formData.sku}
                    onChange={handleInputChange}
                    placeholder="e.g., SP-100"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {/* Price */}
                <div>
                  <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-2">
                    Price (Optional)
                  </label>
                  <input
                    id="price"
                    name="price"
                    type="number"
                    step="0.01"
                    value={formData.price}
                    onChange={handleInputChange}
                    placeholder="e.g., 250.00"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>
              </div>

              {/* Description */}
              <div className="mt-6">
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Description (Optional)
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Product description"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </>
          )}

          {/* API Error */}
          {errors.api && (
            <div className="mt-4 rounded-xl bg-red-500/20 p-4 border border-red-500/30">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg
                    className="h-5 w-5 text-red-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-400">{errors.api}</p>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="mt-6 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="w-full sm:w-auto flex justify-center py-3 px-6 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 transform hover:scale-[1.02]"
            >
              {loading ? (
                <>
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
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
                  Adding...
                </>
              ) : (
                'Add Serialized Item'
              )}
            </button>
          </div>
        </form>
      </div>
    </main>
  );
}
