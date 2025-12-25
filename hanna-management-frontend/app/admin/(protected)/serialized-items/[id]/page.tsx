"use client";

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/app/store/authStore';
import BarcodeScannerButton from '@/app/components/BarcodeScannerButton';

interface ProductOption { id: number; name: string }

export default function EditSerializedItemPage() {
  const { accessToken } = useAuthStore();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [products, setProducts] = useState<ProductOption[]>([]);
  const [formData, setFormData] = useState({
    serial_number: '',
    barcode: '',
    product: '',
    status: 'in_stock',
    current_location: 'warehouse',
    location_notes: '',
  });

  const routeParams = useParams();
  const id = (routeParams?.id as string) || '';

  useEffect(() => {
    const load = async () => {
      if (!accessToken) return;
      if (!id || id === 'undefined' || Number.isNaN(Number(id))) {
        setError('Invalid item id. Please navigate from the list.');
        setLoading(false);
        return;
      }
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        // Load products
        const prodResp = await fetch(`${apiUrl}/crm-api/products/products/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        if (prodResp.ok) {
          const data = await prodResp.json();
          setProducts(data.results || []);
        }

        // Load item
        const itemResp = await fetch(`${apiUrl}/crm-api/products/serialized-items/${id}/`, {
          headers: { 'Authorization': `Bearer ${accessToken}` },
        });
        if (!itemResp.ok) throw new Error(`Failed to load item (${itemResp.status})`);
        const item = await itemResp.json();
        setFormData({
          serial_number: item.serial_number || '',
          barcode: item.barcode || '',
          product: item.product?.id ? String(item.product.id) : '',
          status: item.status || 'in_stock',
          current_location: item.current_location || 'warehouse',
          location_notes: item.location_notes || '',
        });
      } catch (e: any) {
        setError(e.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [accessToken, id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleScanSerial = (code: string) => setFormData(prev => ({ ...prev, serial_number: code }));
  const handleScanBarcode = (code: string) => setFormData(prev => ({ ...prev, barcode: code }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const resp = await fetch(`${apiUrl}/crm-api/products/serialized-items/${id}/`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          serial_number: formData.serial_number,
          barcode: formData.barcode || null,
          product_id: formData.product ? parseInt(formData.product) : null,
          status: formData.status,
          current_location: formData.current_location,
          location_notes: formData.location_notes || '',
        }),
      });
      if (!resp.ok) throw new Error(`Failed to save (${resp.status})`);
      setSuccess('Item updated successfully');
      setTimeout(() => {
        router.push('/admin/serialized-items');
      }, 800);
    } catch (e: any) {
      setError(e.message || 'Failed to save');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="p-4">Loading...</div>;

  return (
    <div className="min-h-screen bg-gray-50 p-4 sm:p-6 lg:p-8">
      <div className="max-w-3xl mx-auto bg-white p-4 sm:p-6 lg:p-8 rounded-lg shadow-md">
        <div className="mb-6 flex justify-between items-center">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Edit Serialized Item</h1>
          <Link href="/admin/serialized-items" className="px-3 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300">Back</Link>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">{error}</div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded text-green-700 text-sm">{success}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700">Serial Number</label>
                <input name="serial_number" value={formData.serial_number} onChange={handleChange} className="mt-1 w-full px-3 py-2 border rounded" />
              </div>
              <BarcodeScannerButton onScanSuccess={handleScanSerial} />
            </div>
            <div className="flex items-end">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700">Barcode</label>
                <input name="barcode" value={formData.barcode} onChange={handleChange} className="mt-1 w-full px-3 py-2 border rounded" />
              </div>
              <BarcodeScannerButton onScanSuccess={handleScanBarcode} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Product</label>
              <select name="product" value={formData.product} onChange={handleChange} className="mt-1 w-full px-3 py-2 border rounded">
                <option value="">Select product</option>
                {(products || []).map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Status</label>
              <select name="status" value={formData.status} onChange={handleChange} className="mt-1 w-full px-3 py-2 border rounded">
                <option value="in_stock">In Stock</option>
                <option value="sold">Sold</option>
                <option value="in_repair">In Repair</option>
                <option value="in_transit">In Transit</option>
                <option value="returned">Returned</option>
                <option value="decommissioned">Decommissioned</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Current Location</label>
              <select name="current_location" value={formData.current_location} onChange={handleChange} className="mt-1 w-full px-3 py-2 border rounded">
                <option value="warehouse">Warehouse</option>
                <option value="store">Store</option>
                <option value="customer">Customer</option>
                <option value="technician">Technician</option>
                <option value="in_transit">In Transit</option>
                <option value="returned">Returned</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Location Notes</label>
              <textarea name="location_notes" value={formData.location_notes} onChange={handleChange} className="mt-1 w-full px-3 py-2 border rounded h-24" />
            </div>
          </div>

          <div className="flex justify-end gap-2">
            <Link href="/admin/serialized-items" className="px-4 py-2 bg-gray-200 text-gray-800 rounded">Cancel</Link>
            <button type="submit" disabled={saving} className="px-4 py-2 bg-purple-600 text-white rounded disabled:opacity-50">
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
