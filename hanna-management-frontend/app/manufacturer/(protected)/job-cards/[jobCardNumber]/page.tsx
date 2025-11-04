'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { FiTool, FiUser, FiSmartphone, FiMapPin, FiAlertCircle, FiFileText, FiCheckSquare, FiTag, FiShield } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface JobCardDetail {
  job_card_number: string;
  customer_name: string;
  customer_whatsapp: string;
  customer_address: string;
  product_description: string;
  product_serial_number: string;
  status: string;
  creation_date: string;
  reported_fault: string;
  is_under_warranty: boolean;
}

const DetailItem = ({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | React.ReactNode }) => (
  <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
    <dt className="text-sm font-medium text-gray-500 flex items-center">{icon}<span className="ml-2">{label}</span></dt>
    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{value || <span className="italic text-gray-400">Not provided</span>}</dd>
  </div>
);

export default function JobCardDetailPage() {
  const params = useParams();
  const router = useRouter();
  const jobCardNumber = params.jobCardNumber as string;

  const [jobCard, setJobCard] = useState<JobCardDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobCardNumber) return;

    const fetchJobCard = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get<JobCardDetail>(`/crm-api/manufacturer/job-cards/${jobCardNumber}/`);
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
    return <div className="flex-1 p-8 text-center">Loading job card details...</div>;
  }

  if (error) {
    return <div className="flex-1 p-8 text-center text-red-500">Error: {error}</div>;
  }

  if (!jobCard) {
    return <div className="flex-1 p-8 text-center">No job card data available.</div>;
  }

  return (
    <main className="flex-1 p-8 overflow-y-auto bg-gray-50">
      <div className="mb-6">
        <Link href="/manufacturer/job-cards" className="text-sm text-purple-600 hover:underline">&larr; Back to Job Cards</Link>
        <div className="flex items-center mt-2">
          <FiTool className="h-8 w-8 mr-3 text-gray-700" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Job Card #{jobCard.job_card_number}</h1>
            <p className="text-sm text-gray-500">Created on: {new Date(jobCard.creation_date).toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h2 className="text-xl font-bold text-gray-800 border-b pb-3 mb-4">Job Details</h2>
          <dl className="divide-y divide-gray-200">
            <DetailItem icon={<FiTag />} label="Product" value={`${jobCard.product_description} (SN: ${jobCard.product_serial_number})`} />
            <DetailItem icon={<FiAlertCircle />} label="Reported Fault" value={<p className="whitespace-pre-wrap">{jobCard.reported_fault}</p>} />
            <DetailItem icon={<FiCheckSquare />} label="Status" value={<span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">{jobCard.status}</span>} />
            <DetailItem icon={<FiShield />} label="Under Warranty" value={jobCard.is_under_warranty ? 'Yes' : 'No'} />
          </dl>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md border border-gray-200">
          <h2 className="text-xl font-bold text-gray-800 border-b pb-3 mb-4">Customer Information</h2>
          <dl className="divide-y divide-gray-200">
            <DetailItem icon={<FiUser />} label="Name" value={jobCard.customer_name} />
            <DetailItem icon={<FiSmartphone />} label="WhatsApp" value={jobCard.customer_whatsapp} />
            <DetailItem icon={<FiMapPin />} label="Address" value={jobCard.customer_address} />
          </dl>
        </div>
      </div>
    </main>
  );
}