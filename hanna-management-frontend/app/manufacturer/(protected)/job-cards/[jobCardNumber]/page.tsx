'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { FiTool } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import JobCardDetail from './JobCardDetail';

interface JobCardDetailData {
  job_card_number: string;
  customer_name: string;
  customer_whatsapp: string;
  customer_address: string;
  serialized_item: {
    serial_number: string;
    product_name: string;
  } | null;
  status: string;
  creation_date: string;
  reported_fault: string;
  is_under_warranty: boolean;
}

export default function JobCardDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobCardNumber = params.jobCardNumber as string;

  const [jobCard, setJobCard] = useState<JobCardDetailData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobCardNumber) return;

    const fetchJobCard = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<JobCardDetailData>(`/crm-api/manufacturer/job-cards/${jobCardNumber}/`);
        setJobCard(response.data);
      } catch (err: any) {
        if (err.response && err.response.status === 404) {
          setError('Job card not found or you do not have permission to view it.');
        } else {
          setError(err.message || 'Failed to fetch job card details.');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchJobCard();
  }, [jobCardNumber]);

  if (loading) {
    return <div className="flex-1 p-4 sm:p-8 text-center">Loading job card details...</div>;
  }

  if (error) {
    return <div className="flex-1 p-4 sm:p-8 text-center text-red-500">Error: {error}</div>;
  }

  if (!jobCard) {
    return <div className="flex-1 p-4 sm:p-8 text-center">No job card data available.</div>;
  }

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto bg-gray-50">
      <div className="mb-6">
        <Link href="/manufacturer/job-cards" className="text-sm text-purple-600 hover:underline">&larr; Back to Job Cards</Link>
        <div className="flex items-center mt-2">
          <FiTool className="h-8 w-8 mr-3 text-gray-700" />
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Job Card #{jobCard.job_card_number}</h1>
            <p className="text-sm text-gray-500">Created on: {new Date(jobCard.creation_date).toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      <JobCardDetail jobCard={jobCard} />
    </main>
  );
}
