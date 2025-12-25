'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiArchive, FiArrowLeft } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';
import BarcodeScannerButton from '@/app/components/BarcodeScannerButton';

interface Product {
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

export default function CreateSerializedItemPage() {
  const [formData, setFormData] = useState({
    serial_number: '',
    barcode: '',
    product: '',
    status: 'in_stock',
  });
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/products/products/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
          },
        });
        if (!response.ok) {
          throw new Error('Failed to fetch products');
        }
        const data = await response.json();
        setProducts(data.results);
      } catch (err: any) {
        setErrors({ api: err.message });
      }
    };
    if (accessToken) {
      fetchProducts();
    }
  }, [accessToken]);

  const validate = () => {
    let tempErrors: any = {};
    if (!formData.serial_number) tempErrors.serial_number = "Serial number is required.";
    if (!formData.product) tempErrors.product = "Product is required.";
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleBarcodeScanned = (barcode: string) => {
    setFormData((prev) => ({
      ...prev,
      serial_number: barcode,
    }));
  };

  const handleBarcodeScannedForBarcode = (barcode: string) => {
    setFormData((prev) => ({
      ...prev,
      barcode,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      
      // Transform formData to match API expectations
      const payload = {
        serial_number: formData.serial_number,
        product_id: parseInt(formData.product), // Send as product_id
        status: formData.status,
      };

      const response = await fetch(`${apiUrl}/crm-api/products/serialized-items/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...payload,
          barcode: formData.barcode || null,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMessage = errorData.detail || errorData.error || JSON.stringify(errorData) || `Failed to create item. Status: ${response.status}`;
        throw new Error(errorMessage);
      }

      router.push('/admin/serialized-items');
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
          <FiArchive className="mr-3" />
          Create Serialized Item
        </h1>
        <Link href="/admin/serialized-items" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-end">
              <InputField id="serial_number" label="Serial Number" value={formData.serial_number} onChange={handleChange} placeholder="e.g., 12345-ABCDE" required error={errors.serial_number} />
              <BarcodeScannerButton onScanSuccess={handleBarcodeScanned} />
            </div>
            <div className="flex items-end">
              <InputField id="barcode" label="Barcode" value={formData.barcode} onChange={handleChange} placeholder="Scan or enter barcode" error={errors.barcode} />
              <BarcodeScannerButton onScanSuccess={handleBarcodeScannedForBarcode} />
            </div>
            <SelectField id="product" label="Product" value={formData.product} onChange={handleChange} error={errors.product}>
                <option value="">Select a product</option>
                {products.map((prod) => (
                  <option key={prod.id} value={prod.id}>{prod.name}</option>
                ))}
            </SelectField>
            <SelectField id="status" label="Status" value={formData.status} onChange={handleChange}>
                <option value="in_stock">In Stock</option>
                <option value="sold">Sold</option>
                <option value="in_repair">In Repair</option>
                <option value="returned">Returned</option>
                <option value="decommissioned">Decommissioned</option>
            </SelectField>
          </div>

          {errors.api && (
            <div className="mt-4 rounded-xl bg-red-500/20 p-4 border border-red-500/30">
                <div className="flex">
                <div className="shrink-0">
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
              ) : 'Create Item'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
