'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiSearch } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface JobCard {
  job_card_number: string;
  customer_name: string;
  customer_whatsapp: string;
  product_description: string;
  product_serial_number: string;
  status: string;
  creation_date: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: JobCard[];
}

const statusColorMap: { [key: string]: string } = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  awaiting_parts: 'bg-purple-100 text-purple-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
};

export default function JobCardsPage() {
  const [jobCards, setJobCards] = useState<JobCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobCards = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<PaginatedResponse>('/crm-api/manufacturer/job-cards/');
        setJobCards(response.data.results);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch job cards.');
      } finally {
        setLoading(false);
      }
    };

    fetchJobCards();
  }, []);

  return (
    <main className="flex-1 p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <FiTool className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-3xl font-bold text-gray-900">Job Cards</h1>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
        {/* Add search and filter controls here later */}
        {loading && <p className="text-center text-gray-500 py-4">Loading job cards...</p>}
        {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
        {!loading && !error && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job Card #</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobCards.map((card) => (
                  <tr key={card.job_card_number} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600">{card.job_card_number}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{card.customer_name}</div>
                      <div className="text-sm text-gray-500">{card.customer_whatsapp}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{card.product_description}</div>
                      <div className="text-sm text-gray-500">SN: {card.product_serial_number}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap"><span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColorMap[card.status] || 'bg-gray-100 text-gray-800'}`}>{card.status}</span></td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{card.creation_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {jobCards.length === 0 && <p className="text-center text-gray-500 py-4">No job cards found.</p>}
          </div>
        )}
      </div>
    </main>
  );
}