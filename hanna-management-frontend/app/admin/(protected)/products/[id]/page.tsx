'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/app/store/authStore';
import { FiPackage, FiTrash2, FiSave, FiArrowLeft } from 'react-icons/fi';
import Link from 'next/link';

interface Product {
  id: number;
  name: string;
  sku: string;
  description: string;
  product_type: string;
  price: string;
  currency: string;
  is_active: boolean;
  stock_quantity: number;
  category: {
    id: number;
    name: string;
  } | null;
  barcode?: string;
  brand?: string;
  country_of_origin?: string;
}

interface Category {
  id: number;
  name: string;
}

export default function EditProductPage({ params }: { params: Promise<{ id: string }> }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    description: '',
    product_type: 'Hardware',
    price: '',
    currency: 'USD',
    is_active: true,
    stock_quantity: 0,
    category: '',
    barcode: '',
    brand: '',
    country_of_origin: '',
  });
  const { accessToken } = useAuthStore();
  const router = useRouter();
  const [productId, setProductId] = useState<string>('');

  useEffect(() => {
    params.then((p) => setProductId(p.id));
  }, [params]);

  useEffect(() => {
    const fetchData = async () => {
      if (!productId || !accessToken) return;

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        
        // Fetch product
        const productResponse = await fetch(`${apiUrl}/crm-api/products/products/${productId}/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!productResponse.ok) {
          throw new Error(`Failed to fetch product. Status: ${productResponse.status}`);
        }

        const productData = await productResponse.json();
        setProduct(productData);
        setFormData({
          name: productData.name || '',
          sku: productData.sku || '',
          description: productData.description || '',
          product_type: productData.product_type || 'Hardware',
          price: productData.price || '',
          currency: productData.currency || 'USD',
          is_active: productData.is_active ?? true,
          stock_quantity: productData.stock_quantity || 0,
          category: productData.category?.id?.toString() || '',
          barcode: productData.barcode || '',
          brand: productData.brand || '',
          country_of_origin: productData.country_of_origin || '',
        });

        // Fetch categories
        const categoriesResponse = await fetch(`${apiUrl}/crm-api/products/categories/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (categoriesResponse.ok) {
          const categoriesData = await categoriesResponse.json();
          setCategories(categoriesData.results || []);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch product');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [productId, accessToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/products/products/${productId}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          category: formData.category ? parseInt(formData.category) : null,
          price: formData.price ? parseFloat(formData.price) : null,
          stock_quantity: parseInt(formData.stock_quantity.toString()),
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update product. Status: ${response.status}`);
      }

      router.push('/admin/products');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update product');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this product? This action cannot be undone.')) {
      return;
    }

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/products/products/${productId}/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete product. Status: ${response.status}`);
      }

      router.push('/admin/products');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete product');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-gray-500">Loading product...</p>
      </div>
    );
  }

  if (error && !product) {
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
          <FiPackage className="mr-3" />
          Edit Product
        </h1>
        <div className="flex gap-2">
          <Link href="/admin/products">
            <span className="flex items-center px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition">
              <FiArrowLeft className="mr-2" />
              Back
            </span>
          </Link>
          <button
            onClick={handleDelete}
            className="flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition"
          >
            <FiTrash2 className="mr-2" />
            Delete
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                Product Name *
              </label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label htmlFor="sku" className="block text-sm font-medium text-gray-700 mb-2">
                SKU *
              </label>
              <input
                type="text"
                id="sku"
                value={formData.sku}
                onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label htmlFor="product_type" className="block text-sm font-medium text-gray-700 mb-2">
                Product Type *
              </label>
              <select
                id="product_type"
                value={formData.product_type}
                onChange={(e) => setFormData({ ...formData, product_type: e.target.value })}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="Hardware">Hardware</option>
                <option value="Software">Software</option>
                <option value="Service">Service</option>
              </select>
            </div>

            <div>
              <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                Category
              </label>
              <select
                id="category"
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="">Select a category</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-2">
                Price
              </label>
              <input
                type="number"
                id="price"
                step="0.01"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-2">
                Currency
              </label>
              <select
                id="currency"
                value={formData.currency}
                onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="USD">USD</option>
                <option value="ZWL">ZWL</option>
                <option value="ZAR">ZAR</option>
              </select>
            </div>

            <div>
              <label htmlFor="stock_quantity" className="block text-sm font-medium text-gray-700 mb-2">
                Stock Quantity
              </label>
              <input
                type="number"
                id="stock_quantity"
                value={formData.stock_quantity}
                onChange={(e) => setFormData({ ...formData, stock_quantity: parseInt(e.target.value) || 0 })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label htmlFor="barcode" className="block text-sm font-medium text-gray-700 mb-2">
                Barcode
              </label>
              <input
                type="text"
                id="barcode"
                value={formData.barcode}
                onChange={(e) => setFormData({ ...formData, barcode: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label htmlFor="brand" className="block text-sm font-medium text-gray-700 mb-2">
                Brand
              </label>
              <input
                type="text"
                id="brand"
                value={formData.brand}
                onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div>
              <label htmlFor="country_of_origin" className="block text-sm font-medium text-gray-700 mb-2">
                Country of Origin
              </label>
              <input
                type="text"
                id="country_of_origin"
                value={formData.country_of_origin}
                onChange={(e) => setFormData({ ...formData, country_of_origin: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                Active
              </label>
            </div>
          </div>

          <div className="col-span-2">
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="description"
              rows={4}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
            />
          </div>

          <div className="flex justify-end gap-3">
            <Link href="/admin/products">
              <span className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition">
                Cancel
              </span>
            </Link>
            <button
              type="submit"
              disabled={saving}
              className="flex items-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition disabled:opacity-50"
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
