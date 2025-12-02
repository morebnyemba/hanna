'use client';

import { useEffect, useState } from 'react';
import { FiList, FiRefreshCw, FiArrowRight } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface HistoryItem {
  id: number;
  serialized_item: {
    product: { name: string };
    serial_number: string;
  };
  from_location: string | null;
  from_location_display: string | null;
  to_location: string;
  to_location_display: string;
  transfer_reason: string;
  transfer_reason_display: string;
  notes: string | null;
  timestamp: string;
}

export default function HistoryPage() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get<HistoryItem[]>('/crm-api/products/retailer-branch/history/');
      setHistory(response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Transaction History</h1>
        <button
          onClick={fetchHistory}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
        >
          <FiRefreshCw className={`mr-2 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="bg-white p-4 rounded-lg shadow-md animate-pulse">
              <div className="space-y-2">
                <div className="h-5 bg-gray-200 rounded w-1/3"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/4"></div>
              </div>
            </div>
          ))}
        </div>
      ) : history.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow-md text-center">
          <FiList className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-800 mb-2">No Transaction History</h3>
          <p className="text-gray-600">Your check-in and checkout history will appear here.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {history.map((item) => (
            <div key={item.id} className="bg-white p-4 rounded-lg shadow-md border-l-4 border-emerald-500">
              <div className="flex flex-col sm:flex-row justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-800">
                    {item.serialized_item?.product?.name || 'Unknown Product'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    SN: {item.serialized_item?.serial_number || 'N/A'}
                  </p>
                  <div className="flex items-center text-sm text-gray-600 mt-2">
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {item.from_location_display || item.from_location || 'N/A'}
                    </span>
                    <FiArrowRight className="mx-2" />
                    <span className="px-2 py-1 bg-emerald-100 text-emerald-800 rounded">
                      {item.to_location_display || item.to_location}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">
                    Reason: {item.transfer_reason_display || item.transfer_reason}
                  </p>
                  {item.notes && (
                    <p className="text-sm text-gray-500 mt-1 italic">&quot;{item.notes}&quot;</p>
                  )}
                </div>
                <div className="text-right mt-2 sm:mt-0">
                  <p className="text-sm text-gray-500">{formatDate(item.timestamp)}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  );
}
