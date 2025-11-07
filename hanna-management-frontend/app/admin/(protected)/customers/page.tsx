'use client';

import { useEffect, useState } from 'react';
import { FiUsers, FiPlus } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';

interface Customer {
  contact: {
    id: number;
    whatsapp_id: string;
    name: string;
  };
  first_name: string;
  last_name: string;
  email: string;
  address_line_1: string;
  address_line_2: string;
  city: string;
  state_province: string;
  postal_code: string;
  country: string;
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
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </td>
        <td className="px-6 py-4 whitespace-nowrap">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
        </td>
    </tr>
);

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/customer-data/profiles/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch data. Status: ${response.status}`);
        }

        const result = await response.json();
        setCustomers(result.results); // Assuming the API returns data in a 'results' property
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchCustomers();
    }
  }, [accessToken]);

  if (error) {
    return <div className="flex items-center justify-center h-full"><p className="text-red-500">Error: {error}</p></div>;
  }

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiUsers className="mr-3" />
          Customers
        </h1>
        <Link href="/admin/customers/create">
          <span className="flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition">
            <FiPlus className="mr-2" />
            Create Customer
          </span>
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
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
                customers.map((customer) => (
                    <tr key={customer.contact.id} className="hover:bg-gray-50 transition-colors duration-150">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            <Link href={`/admin/customers/${customer.contact.id}`} className="text-purple-600 hover:text-purple-800">
                                {customer.first_name && customer.last_name ? `${customer.first_name} ${customer.last_name}` : customer.contact.name}
                            </Link>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.contact.whatsapp_id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{customer.email}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {customer.address_line_1} {customer.address_line_2}, {customer.city}
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
