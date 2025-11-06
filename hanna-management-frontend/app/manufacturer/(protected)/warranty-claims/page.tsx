'use client';

import { useEffect, useState } from 'react';
import { FiShield } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WarrantyClaim[];
}

export default function WarrantyClaimsPage() {
  const [claims, setClaims] = useState<WarrantyClaim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchClaims = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<PaginatedResponse>('/crm-api/manufacturer/warranty-claims/');
        setClaims(response.data.results);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch warranty claims.');
      } finally {
        setLoading(false);
      }
    };

    fetchClaims();
  }, []);

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <FiShield className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Warranty Claims</h1>
        </div>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        {loading && <p className="text-center text-gray-500 py-4">Loading warranty claims...</p>}
        {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
        {!loading && !error && (
          <div className="hidden md:block overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Claim ID</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {claims.map((claim) => (
                  <tr key={claim.claim_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600">{claim.claim_id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{claim.product_name} (SN: {claim.product_serial_number})</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{claim.status}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(claim.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
