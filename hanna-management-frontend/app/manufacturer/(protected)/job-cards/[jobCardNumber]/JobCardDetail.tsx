'use client';

import React from 'react';
import { FiTool, FiUser, FiSmartphone, FiMapPin, FiAlertCircle, FiFileText, FiCheckSquare, FiTag, FiShield } from 'react-icons/fi';

interface JobCardDetail {
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

const DetailItem = ({ icon, label, value }: { icon: React.ReactNode; label: string; value: string | React.ReactNode }) => (
  <div className="py-3 sm:grid sm:grid-cols-3 sm:gap-4">
    <dt className="text-sm font-medium text-gray-500 flex items-center">{icon}<span className="ml-2">{label}</span></dt>
    <dd className="mt-1 text-sm text-gray-900 sm:mt-0 sm:col-span-2">{value || <span className="italic text-gray-400">Not provided</span>}</dd>
  </div>
);

const JobCardDetail = ({ jobCard }: { jobCard: JobCardDetail }) => (
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8">
    <div className="lg:col-span-2 bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
      <h2 className="text-lg sm:text-xl font-bold text-gray-800 border-b pb-3 mb-4">Job Details</h2>
      <dl className="divide-y divide-gray-200">
        <DetailItem icon={<FiTag />} label="Product" value={`${jobCard.serialized_item?.product_name} (SN: ${jobCard.serialized_item?.serial_number})`} />
        <DetailItem icon={<FiAlertCircle />} label="Reported Fault" value={<p className="whitespace-pre-wrap">{jobCard.reported_fault}</p>} />
        <DetailItem icon={<FiCheckSquare />} label="Status" value={<span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-100 text-blue-800">{jobCard.status}</span>} />
        <DetailItem icon={<FiShield />} label="Under Warranty" value={jobCard.is_under_warranty ? 'Yes' : 'No'} />
      </dl>
    </div>

    <div className="bg-white p-4 sm:p-6 rounded-lg shadow-md border border-gray-200">
      <h2 className="text-lg sm:text-xl font-bold text-gray-800 border-b pb-3 mb-4">Customer Information</h2>
      <dl className="divide-y divide-gray-200">
        <DetailItem icon={<FiUser />} label="Name" value={jobCard.customer_name} />
        <DetailItem icon={<FiSmartphone />} label="WhatsApp" value={jobCard.customer_whatsapp} />
        <DetailItem icon={<FiMapPin />} label="Address" value={jobCard.customer_address} />
      </dl>
    </div>
  </div>
);

export default JobCardDetail;
