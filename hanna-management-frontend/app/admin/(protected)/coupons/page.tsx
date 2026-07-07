'use client';

import { useEffect, useState } from 'react';
import { FiTag, FiPlus } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';
import ActionButtons from '@/app/components/shared/ActionButtons';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';

interface Coupon {
  id: number;
  code: string;
  description: string;
  discount_type: 'percentage' | 'fixed' | 'free_shipping';
  discount_value: string;
  max_uses: number | null;
  uses: number;
  is_active: boolean;
  valid_from: string | null;
  valid_until: string | null;
}

const DISCOUNT_LABELS: Record<Coupon['discount_type'], string> = {
  percentage: 'Percentage Off',
  fixed: 'Fixed Amount Off',
  free_shipping: 'Free Shipping',
};

function formatDiscount(coupon: Coupon) {
  if (coupon.discount_type === 'percentage') return `${coupon.discount_value}% off`;
  if (coupon.discount_type === 'fixed') return `$${coupon.discount_value} off`;
  return 'Free shipping';
}

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-1/3"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-1/3"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-1/4"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-1/4"></div></td>
    <td className="px-6 py-4 whitespace-nowrap"><div className="h-4 bg-gray-200 rounded w-1/4"></div></td>
  </tr>
);

export default function CouponsPage() {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [couponToDelete, setCouponToDelete] = useState<Coupon | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const { accessToken } = useAuthStore();

  const fetchCoupons = async () => {
    try {
      const response = await apiClient.get('/crm-api/products/coupons/');
      setCoupons(response.data.results ?? response.data);
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to fetch coupons.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) fetchCoupons();
  }, [accessToken]);

  const handleDeleteClick = (coupon: Coupon) => {
    setCouponToDelete(coupon);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!couponToDelete) return;
    setIsDeleting(true);
    try {
      await apiClient.delete(`/crm-api/products/coupons/${couponToDelete.id}/`);
      setCoupons((prev) => prev.filter((c) => c.id !== couponToDelete.id));
      setDeleteModalOpen(false);
      setCouponToDelete(null);
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to delete coupon.'));
    } finally {
      setIsDeleting(false);
    }
  };

  if (error) {
    return <div className="flex items-center justify-center h-full"><p className="text-red-500">Error: {error}</p></div>;
  }

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTag className="mr-3" />
          Coupons
        </h1>
        <Link href="/admin/coupons/create">
          <span className="flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition">
            <FiPlus className="mr-2" />
            Create Coupon
          </span>
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Discount</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Uses</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <>
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                </>
              ) : coupons.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-400">
                    No coupons yet. Create one to enable discount codes at checkout.
                  </td>
                </tr>
              ) : (
                coupons.map((coupon) => (
                  <tr key={coupon.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono font-semibold text-gray-900">{coupon.code}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatDiscount(coupon)}
                      <span className="block text-xs text-gray-400">{DISCOUNT_LABELS[coupon.discount_type]}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {coupon.uses}{coupon.max_uses ? ` / ${coupon.max_uses}` : ''}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${coupon.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {coupon.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <ActionButtons
                        entityId={coupon.id}
                        editPath={`/admin/coupons/${coupon.id}`}
                        onDelete={() => handleDeleteClick(coupon)}
                        showView={false}
                      />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        onConfirm={handleDeleteConfirm}
        title="Delete Coupon"
        message={`Are you sure you want to delete "${couponToDelete?.code}"? This action cannot be undone.`}
        isDeleting={isDeleting}
      />
    </>
  );
}
