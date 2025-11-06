'use client';

import React from 'react';

interface WarrantyClaim {
  claim_id: string;
  product_name: string;
  product_serial_number: string;
  customer_name: string;
  status: string;
  created_at: string;
}

const RecentClaimsTable = ({ claims }: { claims: WarrantyClaim[] }) => (
  <div className="mt-8 bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
    <div className="flex items-center mb-4">
      <h2 className="text-lg sm:text-xl font-bold text-gray-800">Recent Warranty Claims</h2>
    </div>
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
  </div>
);

export default RecentClaimsTable;
