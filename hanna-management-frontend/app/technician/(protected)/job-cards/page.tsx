'use client';

import { useEffect, useState, useCallback } from 'react';
import { FiTool, FiUser, FiPackage, FiCalendar, FiAlertCircle, FiPhone } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface JobCard {
  id: number;
  job_card_number: string;
  customer_name: string;
  customer_whatsapp: string;
  serialized_item: {
    serial_number: string;
    product_name: string;
  } | null;
  status: string;
  status_display?: string;
  fault_description: string;
  creation_date: string;
  priority?: string;
}

const statusColorMap: { [key: string]: string } = {
  open: 'bg-blue-100 text-blue-800',
  pending: 'bg-yellow-100 text-yellow-800',
  in_progress: 'bg-purple-100 text-purple-800',
  awaiting_parts: 'bg-orange-100 text-orange-800',
  resolved: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-800',
};

const priorityColorMap: { [key: string]: string } = {
  low: 'border-green-500',
  normal: 'border-blue-500',
  high: 'border-orange-500',
  urgent: 'border-red-500',
};

const SkeletonCard = () => (
  <div className="bg-white shadow rounded-lg p-4 border border-gray-200 animate-pulse">
    <div className="flex justify-between items-center">
      <div className="h-4 bg-gray-200 rounded w-1/4"></div>
      <div className="h-6 bg-gray-200 rounded-full w-16"></div>
    </div>
    <div className="mt-3 space-y-2">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
      <div className="h-4 bg-gray-200 rounded w-full"></div>
    </div>
  </div>
);

export default function TechnicianJobCardsPage() {
  const [jobCards, setJobCards] = useState<JobCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const { accessToken } = useAuthStore();

  const fetchJobCards = useCallback(async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/technician/job-cards/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch job cards. Status: ${response.status}`);
      }

      const result = await response.json();
      setJobCards(result.results || result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    if (accessToken) {
      fetchJobCards();
    }
  }, [accessToken, fetchJobCards]);

  const filteredJobCards = statusFilter === 'all' 
    ? jobCards 
    : jobCards.filter(card => card.status === statusFilter);

  const openCount = jobCards.filter(c => c.status === 'open' || c.status === 'pending').length;
  const inProgressCount = jobCards.filter(c => c.status === 'in_progress').length;
  const awaitingPartsCount = jobCards.filter(c => c.status === 'awaiting_parts').length;

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="mb-6">
          <div className="h-8 bg-gray-200 rounded w-48 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center gap-2">
          <FiAlertCircle className="w-5 h-5" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTool className="mr-3 h-8 w-8" />
          My Job Cards
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Repair and service jobs assigned to you.
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-blue-700">{openCount}</p>
          <p className="text-sm text-blue-600">Open</p>
        </div>
        <div className="bg-purple-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-purple-700">{inProgressCount}</p>
          <p className="text-sm text-purple-600">In Progress</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-4 text-center">
          <p className="text-2xl font-bold text-orange-700">{awaitingPartsCount}</p>
          <p className="text-sm text-orange-600">Awaiting Parts</p>
        </div>
      </div>

      {/* Filter */}
      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="w-full sm:w-auto px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500"
        >
          <option value="all">All Statuses ({jobCards.length})</option>
          <option value="open">Open ({jobCards.filter(c => c.status === 'open').length})</option>
          <option value="pending">Pending ({jobCards.filter(c => c.status === 'pending').length})</option>
          <option value="in_progress">In Progress ({inProgressCount})</option>
          <option value="awaiting_parts">Awaiting Parts ({awaitingPartsCount})</option>
          <option value="resolved">Resolved ({jobCards.filter(c => c.status === 'resolved').length})</option>
        </select>
      </div>

      {/* Job Cards Grid */}
      {filteredJobCards.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiTool className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No job cards found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {statusFilter === 'all' 
              ? "You don't have any job cards assigned yet."
              : `No job cards with status "${statusFilter}".`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredJobCards.map((card) => (
            <div
              key={card.id || card.job_card_number}
              className={`bg-white shadow rounded-lg p-4 border-l-4 ${priorityColorMap[card.priority || 'normal'] || 'border-gray-300'} hover:shadow-lg transition-shadow`}
            >
              <div className="flex justify-between items-start mb-3">
                <div>
                  <span className="text-sm font-medium text-green-600">{card.job_card_number}</span>
                  <span className={`ml-2 px-2 py-0.5 text-xs font-semibold rounded-full ${statusColorMap[card.status] || 'bg-gray-100 text-gray-800'}`}>
                    {card.status_display || card.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="flex items-center text-xs text-gray-500">
                  <FiCalendar className="mr-1 w-3 h-3" />
                  {new Date(card.creation_date).toLocaleDateString()}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex items-start">
                  <FiUser className="mr-2 w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">{card.customer_name}</p>
                    <a 
                      href={`tel:${card.customer_whatsapp}`}
                      className="text-xs text-green-600 hover:text-green-800 flex items-center"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <FiPhone className="mr-1 w-3 h-3" />
                      {card.customer_whatsapp}
                    </a>
                  </div>
                </div>

                {card.serialized_item && (
                  <div className="flex items-start">
                    <FiPackage className="mr-2 w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-sm text-gray-900">{card.serialized_item.product_name}</p>
                      <p className="text-xs text-gray-500">SN: {card.serialized_item.serial_number}</p>
                    </div>
                  </div>
                )}

                {card.fault_description && (
                  <div className="mt-2 pt-2 border-t">
                    <p className="text-xs text-gray-600 overflow-hidden" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      <strong>Issue:</strong> {card.fault_description}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
