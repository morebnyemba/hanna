'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuthStore } from '@/app/store/authStore';
import { FiTag, FiArrowLeft, FiSave } from 'react-icons/fi';
import { InputField, SelectField, TextAreaField } from '@/app/components/forms/FormComponents';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';

function toDatetimeLocal(value: string | null): string {
  if (!value) return '';
  // value is an ISO string from the API; datetime-local inputs want
  // "YYYY-MM-DDTHH:mm" with no timezone suffix.
  const d = new Date(value);
  if (isNaN(d.getTime())) return '';
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function EditCouponPage({ params }: { params: Promise<{ id: string }> }) {
  const [couponId, setCouponId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uses, setUses] = useState(0);
  const [formData, setFormData] = useState({
    code: '',
    description: '',
    discount_type: 'percentage',
    discount_value: '',
    minimum_order_amount: '0',
    max_uses: '',
    max_uses_per_customer: '1',
    is_active: true,
    valid_from: '',
    valid_until: '',
  });
  const { accessToken } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    params.then((p) => setCouponId(p.id));
  }, [params]);

  useEffect(() => {
    const fetchCoupon = async () => {
      if (!couponId || !accessToken) return;
      try {
        const response = await apiClient.get(`/crm-api/products/coupons/${couponId}/`);
        const data = response.data;
        setUses(data.uses ?? 0);
        setFormData({
          code: data.code || '',
          description: data.description || '',
          discount_type: data.discount_type || 'percentage',
          discount_value: data.discount_value ?? '',
          minimum_order_amount: data.minimum_order_amount ?? '0',
          max_uses: data.max_uses != null ? String(data.max_uses) : '',
          max_uses_per_customer: data.max_uses_per_customer != null ? String(data.max_uses_per_customer) : '1',
          is_active: !!data.is_active,
          valid_from: toDatetimeLocal(data.valid_from),
          valid_until: toDatetimeLocal(data.valid_until),
        });
      } catch (err: unknown) {
        setError(extractErrorMessage(err, 'Failed to fetch coupon.'));
      } finally {
        setLoading(false);
      }
    };
    if (couponId && accessToken) fetchCoupon();
  }, [couponId, accessToken]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.valid_from && formData.valid_until && new Date(formData.valid_from) >= new Date(formData.valid_until)) {
      setError('Valid until date must be after valid from date.');
      return;
    }
    setSaving(true);
    setError(null);

    try {
      await apiClient.put(`/crm-api/products/coupons/${couponId}/`, {
        ...formData,
        code: formData.code.trim().toUpperCase(),
        discount_value: formData.discount_value || '0',
        max_uses: formData.max_uses ? Number(formData.max_uses) : null,
        max_uses_per_customer: Number(formData.max_uses_per_customer) || 1,
        valid_from: formData.valid_from ? new Date(formData.valid_from).toISOString() : null,
        valid_until: formData.valid_until ? new Date(formData.valid_until).toISOString() : null,
      });
      router.push('/admin/coupons');
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to update coupon.'));
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

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTag className="mr-3" />
          Edit Coupon
        </h1>
        <Link href="/admin/coupons">
          <span className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition">
            <FiArrowLeft className="mr-2" />
            Back to Coupons
          </span>
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputField id="code" label="Coupon Code" value={formData.code} onChange={handleChange} required />
            <SelectField id="discount_type" label="Discount Type" value={formData.discount_type} onChange={handleChange}>
              <option value="percentage">Percentage Off</option>
              <option value="fixed">Fixed Amount Off</option>
              <option value="free_shipping">Free Shipping</option>
            </SelectField>

            {formData.discount_type !== 'free_shipping' && (
              <InputField
                id="discount_value"
                label={formData.discount_type === 'percentage' ? 'Discount (%)' : 'Discount Amount ($)'}
                type="number"
                value={formData.discount_value}
                onChange={handleChange}
                required
              />
            )}
            <InputField id="minimum_order_amount" label="Minimum Order Amount ($)" type="number" value={formData.minimum_order_amount} onChange={handleChange} />

            <InputField id="max_uses" label="Max Total Uses (blank = unlimited)" type="number" value={formData.max_uses} onChange={handleChange} />
            <InputField id="max_uses_per_customer" label="Max Uses Per Customer" type="number" value={formData.max_uses_per_customer} onChange={handleChange} />

            <InputField id="valid_from" label="Valid From" type="datetime-local" value={formData.valid_from} onChange={handleChange} />
            <InputField id="valid_until" label="Valid Until" type="datetime-local" value={formData.valid_until} onChange={handleChange} />

            <div className="md:col-span-2">
              <TextAreaField id="description" label="Description (internal note)" value={formData.description} onChange={handleChange} />
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData((prev) => ({ ...prev, is_active: e.target.checked }))}
                className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <label htmlFor="is_active" className="text-sm font-medium text-gray-700">Active</label>
            </div>
            <p className="text-sm text-gray-500 self-center">Redeemed <span className="font-semibold text-gray-700">{uses}</span> time{uses === 1 ? '' : 's'} so far.</p>
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <Link href="/admin/coupons">
              <span className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition">Cancel</span>
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
