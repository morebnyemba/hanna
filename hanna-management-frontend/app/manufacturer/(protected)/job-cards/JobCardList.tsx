'use client';

import React from 'react';
import { useRouter } from 'next/navigation';

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

const statusColorMap: { [key: string]: string } = {
  open: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  awaiting_parts: 'bg-purple-100 text-purple-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
};

const JobCardList = ({ jobCards }: { jobCards: JobCard[] }) => {
  const router = useRouter();

  return (
    <div>
      {/* Table for medium screens and up */}
      <div className="hidden md:block overflow-x-auto">
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
              <tr
                key={card.job_card_number}
                className="hover:bg-gray-50 cursor-pointer"
                onClick={() => router.push(`/manufacturer/job-cards/${card.job_card_number}`)}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-purple-600">{card.job_card_number}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">{card.customer_name}</div>
                  <div className="text-sm text-gray-500">{card.customer_whatsapp}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{card.serialized_item?.product_name}</div>
                  <div className="text-sm text-gray-500">SN: {card.serialized_item?.serial_number}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap"><span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColorMap[card.status] || 'bg-gray-100 text-gray-800'}`}>{card.status}</span></td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{card.creation_date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* Cards for small screens */}
      <div className="md:hidden">
        {jobCards.map((card) => (
          <div key={card.job_card_number} className="bg-white shadow rounded-lg p-4 mb-4 border border-gray-200" onClick={() => router.push(`/manufacturer/job-cards/${card.job_card_number}`)}>
            <div className="flex justify-between items-center">
              <div className="text-sm font-medium text-purple-600">{card.job_card_number}</div>
              <div className="text-sm text-gray-500">{card.creation_date}</div>
            </div>
            <div className="text-sm font-medium text-gray-900 mt-1">{card.customer_name}</div>
            <div className="text-sm text-gray-500">{card.customer_whatsapp}</div>
            <div className="text-sm text-gray-900 mt-1">{card.serialized_item?.product_name} (SN: {card.serialized_item?.serial_number})</div>
            <div className="mt-2 flex justify-between items-center">
              <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusColorMap[card.status] || 'bg-gray-100 text-gray-800'}`}>{card.status}</span>
            </div>
          </div>
        ))}
      </div>
      {jobCards.length === 0 && <p className="text-center text-gray-500 py-4">No job cards found.</p>}
    </div>
  );
};

export default JobCardList;
