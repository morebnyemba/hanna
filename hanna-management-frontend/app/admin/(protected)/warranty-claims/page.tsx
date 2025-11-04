'use client';

import { useEffect, useState } from 'react';
import { FiShield } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

export default function WarrantyClaimsPage() {
  const [claims, setClaims] = useState<WarrantyClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchClaims = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/warranty/claims/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch data. Status: ${response.status}`);
        }

        const result = await response.json();
        setClaims(result.results);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchClaims();
    }
  }, [accessToken]);

  if (loading) {
    return <div className="flex items-center justify-center h-full"><p>Loading Warranty Claims...</p></div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-full"><p className="text-red-500">Error: {error}</p></div>;
  }

  return (
    <>
      <div className="mb-6 flex justify-between items-center">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiShield className="mr-3" />
          Warranty Claims
        </h1>
        <Link href="/admin/warranty-claims/create">
          <span className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
            Create Claim
          </span>
        </Link>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Claim ID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Serial Number</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {claims.map((claim) => (
                <tr key={claim.claim_id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{claim.claim_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{claim.product_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{claim.product_serial_number}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{claim.customer_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{claim.status}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(claim.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}