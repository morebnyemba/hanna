'use client';

import { useEffect, useState } from 'react';
import { FiBox, FiAlertTriangle, FiCheckCircle, FiClock, FiShield } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface ManufacturerStats {
  total_orders: number;
  pending_orders: number;
  completed_orders: number;
  warranty_claims: number;
}

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

interface PaginatedClaimsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: WarrantyClaim[];
}



const StatCard = ({ icon, title, value, color }: { icon: React.ReactNode, title: string, value: number, color: string }) => (

  <div className={`bg-white p-4 sm:p-6 rounded-lg shadow-md border-l-4 ${color}`}>

    <div className="flex items-center">

      <div className="mr-3 sm:mr-4">{icon}</div>

      <div>

        <p className="text-xs sm:text-sm font-medium text-gray-500 uppercase">{title}</p>

        <p className="text-xl sm:text-2xl font-bold text-gray-900">{value}</p>

      </div>

    </div>

  </div>

);



export default function ManufacturerDashboardPage() {

  const [stats, setStats] = useState<ManufacturerStats | null>(null);

  const [claims, setClaims] = useState<WarrantyClaim[]>([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState<string | null>(null);



  useEffect(() => {

    const fetchData = async () => {

      setLoading(true);

      setError(null);

      try {

        // Fetch stats and recent claims in parallel

        const [statsResponse, claimsResponse] = await Promise.all([

          apiClient.get<ManufacturerStats>('/crm-api/manufacturer/dashboard-stats/'),

          apiClient.get<PaginatedClaimsResponse>('/crm-api/manufacturer/warranty-claims/?page_size=5') // Fetch only 5 for the dashboard

        ]);

        setStats(statsResponse.data);

        setClaims(claimsResponse.data.results);

      } catch (err: any) {

        setError(err.message || 'Failed to fetch dashboard data.');

      } finally {

        setLoading(false);

      }

    };



    fetchData();

  }, []);



  return (

    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">

      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">Manufacturer Dashboard</h1>

      {loading && <p className="text-center text-gray-500">Loading dashboard...</p>}

      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      {!loading && !error && stats && (

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">

        <StatCard icon={<FiBox size={24} className="text-blue-500" />} title="Total Orders" value={stats?.total_orders ?? 0} color="border-blue-500" />

        <StatCard icon={<FiClock size={24} className="text-yellow-500" />} title="Pending Orders" value={stats?.pending_orders ?? 0} color="border-yellow-500" />

        <StatCard icon={<FiCheckCircle size={24} className="text-green-500" />} title="Completed Orders" value={stats?.completed_orders ?? 0} color="border-green-500" />

        <StatCard icon={<FiAlertTriangle size={24} className="text-red-500" />} title="Warranty Claims" value={stats?.warranty_claims ?? 0} color="border-red-500" />

      </div>

      )}



      {/* Recent Warranty Claims Table */}

      <div className="mt-8 bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">

        <div className="flex items-center mb-4">

          <FiShield className="h-6 w-6 mr-3 text-gray-700" />

          <h2 className="text-lg sm:text-xl font-bold text-gray-800">Recent Warranty Claims</h2>

        </div>

        {!loading && !error && (

          <div>

            {/* Table for medium screens and up */}

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

            {/* Cards for small screens */}

            <div className="md:hidden">

              {claims.map((claim) => (

                <div key={claim.claim_id} className="bg-white shadow rounded-lg p-4 mb-4 border border-gray-200">

                  <div className="flex justify-between items-center">

                    <div className="text-sm font-medium text-purple-600">{claim.claim_id}</div>

                    <div className="text-sm text-gray-500">{new Date(claim.created_at).toLocaleDateString()}</div>

                  </div>

                  <div className="text-sm text-gray-900 mt-1">{claim.product_name} (SN: {claim.product_serial_number})</div>

                  <div className="mt-2 flex justify-between items-center">

                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">

                      {claim.status}

                    </span>

                  </div>

                </div>

              ))}

            </div>

            {claims.length === 0 && <p className="text-center text-gray-500 py-4">No recent warranty claims found.</p>}

          </div>

        )}

      </div>

    </main>

  );

}
