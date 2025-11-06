'use client';

import { useEffect, useState } from 'react';
import { FiTool } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import JobCardList from './JobCardList';

interface JobCard {
  job_card_number: string;
  customer_name: string;
  customer_whatsapp: string;
  serialized_item: {
    serial_number: string;
    product_name: string;
  } | null;
  status: string;
  creation_date: string;
}

interface PaginatedResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: JobCard[];
}

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
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center">
          <FiTool className="h-8 w-8 mr-3 text-gray-700" />
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Job Cards</h1>
        </div>
      </div>

      <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
        {loading && <p className="text-center text-gray-500 py-4">Loading job cards...</p>}
        {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}
        {!loading && !error && <JobCardList jobCards={jobCards} />}
      </div>
    </main>
  );
}
