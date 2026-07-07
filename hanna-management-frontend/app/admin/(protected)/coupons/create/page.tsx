'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { FiTag, FiArrowLeft } from 'react-icons/fi';
import Link from 'next/link';
import { InputField, SelectField, TextAreaField } from '@/app/components/forms/FormComponents';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';

export default function CreateCouponPage() {
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
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  const router = useRouter();

  const validate = () => {
    const tempErrors: any = {};
    if (!formData.code.trim()) tempErrors.code = 'Coupon code is required.';
    if (formData.discount_type !== 'free_shipping' && !formData.discount_value) {
      tempErrors.discount_value = 'Discount value is required.';
    }
    if (formData.valid_from && formData.valid_until && new Date(formData.valid_from) >= new Date(formData.valid_until)) {
      tempErrors.valid_until = 'Valid until date must be after valid from date.';
    }
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    setErrors({});

    try {
      await apiClient.post('/crm-api/products/coupons/', {
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
      setErrors({ api: extractErrorMessage(err, 'Failed to create coupon.') });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTag className="mr-3" />
          Create Coupon
        </h1>
        <Link href="/admin/coupons" className="flex items-center justify-center px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 transition">
          <FiArrowLeft className="mr-2" />
          Back to List
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <InputField id="code" label="Coupon Code" value={formData.code} onChange={handleChange} placeholder="e.g., SAVE10" required error={errors.code} />
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
                placeholder={formData.discount_type === 'percentage' ? '10' : '5.00'}
                required
                error={errors.discount_value}
              />
            )}
            <InputField id="minimum_order_amount" label="Minimum Order Amount ($)" type="number" value={formData.minimum_order_amount} onChange={handleChange} placeholder="0" />

            <InputField id="max_uses" label="Max Total Uses (blank = unlimited)" type="number" value={formData.max_uses} onChange={handleChange} placeholder="e.g., 100" />
            <InputField id="max_uses_per_customer" label="Max Uses Per Customer" type="number" value={formData.max_uses_per_customer} onChange={handleChange} placeholder="1" />

            <InputField id="valid_from" label="Valid From" type="datetime-local" value={formData.valid_from} onChange={handleChange} />
            <InputField id="valid_until" label="Valid Until" type="datetime-local" value={formData.valid_until} onChange={handleChange} />

            <div className="md:col-span-2">
              <TextAreaField id="description" label="Description (internal note)" value={formData.description} onChange={handleChange} placeholder="e.g., Black Friday 2026 promo" />
            </div>

            <div className="md:col-span-2 flex items-center gap-3">
              <input
                type="checkbox"
                id="is_active"
                checked={formData.is_active}
                onChange={(e) => setFormData((prev) => ({ ...prev, is_active: e.target.checked }))}
                className="h-4 w-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
              />
              <label htmlFor="is_active" className="text-sm font-medium text-gray-700">Active</label>
            </div>
          </div>

          {errors.api && (
            <div className="mt-4 rounded-xl bg-red-500/20 p-4 border border-red-500/30">
              <p className="text-sm text-red-500">{errors.api}</p>
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <button type="submit" disabled={loading} className="w-full sm:w-auto flex justify-center py-3 px-6 border border-transparent rounded-xl shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300">
              {loading ? 'Creating...' : 'Create Coupon'}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
