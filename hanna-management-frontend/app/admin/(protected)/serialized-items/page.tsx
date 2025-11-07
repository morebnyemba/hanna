'use client';

import { useEffect, useState } from 'react';
import { FiArchive, FiPlus } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';

interface SerializedItem {
  id: number;
  serial_number: string;
  status: string;
  product: {
    id: number;
    name: string;
  };
}

const SkeletonRow = () => (
    <tr className="animate-pulse">
        <td className="px-6 py-4 whitespace-nowrap">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
        </td>
    </tr>
);

export default function SerializedItemsPage() {
  const [items, setItems] = useState<SerializedItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchItems = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/products/serialized-items/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch data. Status: ${response.status}`);
        }

        const result = await response.json();
        setItems(result.results);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchItems();
    }
  }, [accessToken]);

  if (error) {
    return <div className="flex items-center justify-center h-full"><p className="text-red-500">Error: {error}</p></div>;
  }

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiArchive className="mr-3" />
          Serialized Items
        </h1>
        <Link href="/admin/serialized-items/create">
          <span className="flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition">
            <FiPlus className="mr-2" />
            Create Item
          </span>
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serial Number</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
                {loading ? (
                    <>
                        <SkeletonRow />
                        <SkeletonRow />
                        <SkeletonRow />
                        <SkeletonRow />
                        <SkeletonRow />
                    </>
                ) : (
                    items.map((item) => (
                        <tr key={item.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.serial_number}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.product?.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${item.status === 'in_stock' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                                {item.status.replace('_', ' ')}
                            </span>
                        </td>
                        </tr>
                    ))
                )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
