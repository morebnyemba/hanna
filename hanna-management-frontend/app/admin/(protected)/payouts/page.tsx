'use client';

import { useEffect, useState } from 'react';
import { FiDollarSign, FiCheck, FiX, FiClock, FiUser, FiCalendar, FiAlertCircle } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Payout {
  id: string;
  technician_name: string;
  technician_phone: string;
  amount: string;
  currency: string;
  status: string;
  job_card_count: number;
  installation_count: number;
  period_start: string;
  period_end: string;
  created_at: string;
  approved_at: string | null;
  approved_by_name: string | null;
  notes: string | null;
}

export default function AdminPayoutsPage() {
  const [payouts, setPayouts] = useState<Payout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('pending');
  const [processingId, setProcessingId] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  const fetchPayouts = async () => {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/admin/technician-payouts/?status=${filter}`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch payouts. Status: ${response.status}`);
      }

      const result = await response.json();
      setPayouts(result.results || result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchPayouts();
    }
  }, [accessToken, filter]);

  const handleApprove = async (payoutId: string) => {
    if (!confirm('Approve this payout? This action cannot be undone.')) return;

    setProcessingId(payoutId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/admin/technician-payouts/${payoutId}/approve/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to approve payout');
      }

      alert('Payout approved successfully!');
      await fetchPayouts();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const handleReject = async (payoutId: string) => {
    const reason = prompt('Enter rejection reason:');
    if (!reason) return;

    setProcessingId(payoutId);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/api/admin/technician-payouts/${payoutId}/reject/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        throw new Error('Failed to reject payout');
      }

      alert('Payout rejected.');
      await fetchPayouts();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    } finally {
      setProcessingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: <FiClock className="mr-1" />, text: 'Pending' },
      approved: { color: 'bg-green-100 text-green-800 border-green-200', icon: <FiCheck className="mr-1" />, text: 'Approved' },
      rejected: { color: 'bg-red-100 text-red-800 border-red-200', icon: <FiX className="mr-1" />, text: 'Rejected' },
      paid: { color: 'bg-blue-100 text-blue-800 border-blue-200', icon: <FiCheck className="mr-1" />, text: 'Paid' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${config.color}`}>
        {config.icon}
        {config.text}
      </span>
    );
  };

  const statusCounts = {
    pending: payouts.filter(p => p.status === 'pending').length,
    approved: payouts.filter(p => p.status === 'approved').length,
    rejected: payouts.filter(p => p.status === 'rejected').length,
    paid: payouts.filter(p => p.status === 'paid').length,
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiDollarSign className="mr-3 h-8 w-8 text-green-600" />
          Technician Payouts
        </h1>
        <p className="mt-2 text-sm text-gray-700">
          Review and approve technician payout requests.
        </p>
      </div>

      {/* Status Filter Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { key: 'pending', label: 'Pending', count: statusCounts.pending },
            { key: 'approved', label: 'Approved', count: statusCounts.approved },
            { key: 'paid', label: 'Paid', count: statusCounts.paid },
            { key: 'rejected', label: 'Rejected', count: statusCounts.rejected },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setFilter(tab.key)}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                filter === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`ml-2 py-0.5 px-2 rounded-full text-xs ${
                  filter === tab.key ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Payouts List */}
      {payouts.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiDollarSign className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No payouts found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No {filter} payouts at this time.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {payouts.map((payout) => (
            <div
              key={payout.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                {/* Technician Info */}
                <div className="flex-1 mb-4 lg:mb-0">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 flex items-center">
                        <FiUser className="mr-2 text-gray-400" />
                        {payout.technician_name}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">{payout.technician_phone}</p>
                    </div>
                    <div className="ml-4">
                      {getStatusBadge(payout.status)}
                    </div>
                  </div>

                  <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Period</p>
                      <p className="text-gray-900 font-medium flex items-center">
                        <FiCalendar className="mr-1 text-gray-400" />
                        {new Date(payout.period_start).toLocaleDateString()} - {new Date(payout.period_end).toLocaleDateString()}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-500">Work Completed</p>
                      <p className="text-gray-900 font-medium">
                        {payout.job_card_count} jobs, {payout.installation_count} installations
                      </p>
                    </div>
                  </div>

                  {payout.notes && (
                    <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded">
                      <p className="text-sm text-yellow-800 flex items-start">
                        <FiAlertCircle className="mr-2 mt-0.5 flex-shrink-0" />
                        <span>{payout.notes}</span>
                      </p>
                    </div>
                  )}

                  {payout.approved_at && (
                    <div className="mt-2 text-xs text-gray-500">
                      Approved by {payout.approved_by_name} on {new Date(payout.approved_at).toLocaleString()}
                    </div>
                  )}
                </div>

                {/* Amount & Actions */}
                <div className="lg:ml-6 pt-4 lg:pt-0 border-t lg:border-t-0 lg:border-l lg:pl-6">
                  <div className="text-center lg:text-right mb-4">
                    <p className="text-sm text-gray-500">Payout Amount</p>
                    <p className="text-3xl font-bold text-green-600">
                      {parseFloat(payout.amount).toLocaleString()} {payout.currency}
                    </p>
                  </div>

                  {payout.status === 'pending' && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApprove(payout.id)}
                        disabled={processingId === payout.id}
                        className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                      >
                        <FiCheck className="mr-2" />
                        Approve
                      </button>
                      <button
                        onClick={() => handleReject(payout.id)}
                        disabled={processingId === payout.id}
                        className="flex-1 bg-red-600 hover:bg-red-700 disabled:bg-gray-400 text-white font-semibold py-2 px-4 rounded-lg flex items-center justify-center transition-colors"
                      >
                        <FiX className="mr-2" />
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
