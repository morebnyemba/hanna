'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiAlertCircle, FiCheck, FiClock, FiMapPin } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';

interface Installation {
  id: string;
  installation_type: string;
  system_size: number;
  capacity_unit: string;
  installation_address: string;
}

interface ServiceRequest {
  id: string;
  request_type: string;
  priority: string;
  status: string;
  description: string;
  installation_address: string;
  created_at: string;
  estimated_response_time: string | null;
}

export default function ClientServiceRequestsPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [serviceRequests, setServiceRequests] = useState<ServiceRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  const [formData, setFormData] = useState({
    installation_id: '',
    request_type: 'service',
    priority: 'medium',
    description: '',
    preferred_date: '',
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        
        // Fetch installations
        const installationsResponse = await fetch(`${apiUrl}/crm-api/client/installations/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (installationsResponse.ok) {
          const installationsData = await installationsResponse.json();
          setInstallations(installationsData.results || installationsData);
        }

        // Fetch service requests
        const requestsResponse = await fetch(`${apiUrl}/crm-api/client/service-requests/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (requestsResponse.ok) {
          const requestsData = await requestsResponse.json();
          setServiceRequests(requestsData.results || requestsData);
        }
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchData();
    }
  }, [accessToken]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
      const response = await fetch(`${apiUrl}/crm-api/client/service-requests/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to submit service request');
      }

      alert('Service request submitted successfully!');
      setShowForm(false);
      setFormData({
        installation_id: '',
        request_type: 'service',
        priority: 'medium',
        description: '',
        preferred_date: '',
      });

      // Refresh service requests
      const requestsResponse = await fetch(`${apiUrl}/crm-api/client/service-requests/`, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (requestsResponse.ok) {
        const requestsData = await requestsResponse.json();
        setServiceRequests(requestsData.results || requestsData);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', icon: <FiClock className="mr-1" />, text: 'Pending' },
      assigned: { color: 'bg-blue-100 text-blue-800', icon: <FiClock className="mr-1" />, text: 'Assigned' },
      in_progress: { color: 'bg-purple-100 text-purple-800', icon: <FiClock className="mr-1" />, text: 'In Progress' },
      completed: { color: 'bg-green-100 text-green-800', icon: <FiCheck className="mr-1" />, text: 'Completed' },
      cancelled: { color: 'bg-red-100 text-red-800', icon: <FiAlertCircle className="mr-1" />, text: 'Cancelled' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold ${config.color}`}>
        {config.icon}
        {config.text}
      </span>
    );
  };

  const getPriorityBadge = (priority: string) => {
    const priorityConfig: Record<string, { color: string; text: string }> = {
      low: { color: 'bg-gray-100 text-gray-800', text: 'Low' },
      medium: { color: 'bg-blue-100 text-blue-800', text: 'Medium' },
      high: { color: 'bg-orange-100 text-orange-800', text: 'High' },
      urgent: { color: 'bg-red-100 text-red-800', text: 'Urgent' },
    };

    const config = priorityConfig[priority] || priorityConfig.medium;
    
    return (
      <span className={`inline-flex px-2 py-1 rounded text-xs font-semibold ${config.color}`}>
        {config.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
            <FiTool className="mr-3 h-8 w-8 text-blue-600" />
            Service Requests
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            Submit and track service requests for your solar installations.
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg flex items-center transition-colors"
        >
          <FiTool className="mr-2" />
          New Service Request
        </button>
      </div>

      {error && (
        <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded flex items-center">
          <FiAlertCircle className="mr-2" />
          {error}
        </div>
      )}

      {/* Service Request Form */}
      {showForm && (
        <div className="mb-6 bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Submit Service Request</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Installation *
              </label>
              <select
                required
                value={formData.installation_id}
                onChange={(e) => setFormData({ ...formData, installation_id: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Choose an installation...</option>
                {installations.map((installation) => (
                  <option key={installation.id} value={installation.id}>
                    {installation.installation_type} - {installation.system_size} {installation.capacity_unit} ({installation.installation_address})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Request Type *
                </label>
                <select
                  required
                  value={formData.request_type}
                  onChange={(e) => setFormData({ ...formData, request_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="service">Service Request</option>
                  <option value="repair">Repair</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="inspection">Inspection</option>
                  <option value="warranty_claim">Warranty Claim</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Priority *
                </label>
                <select
                  required
                  value={formData.priority}
                  onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description *
              </label>
              <textarea
                required
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Describe the issue or service needed..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Date
              </label>
              <input
                type="date"
                value={formData.preferred_date}
                onChange={(e) => setFormData({ ...formData, preferred_date: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={submitting}
                className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors"
              >
                {submitting ? 'Submitting...' : 'Submit Request'}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Service Requests List */}
      {serviceRequests.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiTool className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No service requests yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Submit a service request when you need assistance with your solar installation.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {serviceRequests.map((request) => (
            <div
              key={request.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between">
                <div className="flex-1 mb-4 lg:mb-0">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        {request.request_type.replace('_', ' ').toUpperCase()}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1 flex items-center">
                        <FiMapPin className="mr-1" />
                        {request.installation_address}
                      </p>
                    </div>
                    <div className="ml-4 flex gap-2">
                      {getPriorityBadge(request.priority)}
                      {getStatusBadge(request.status)}
                    </div>
                  </div>

                  <div className="mt-3">
                    <p className="text-sm text-gray-700">{request.description}</p>
                  </div>

                  <div className="mt-3 flex items-center text-sm text-gray-500">
                    <FiClock className="mr-1" />
                    Submitted: {new Date(request.created_at).toLocaleDateString()} at {new Date(request.created_at).toLocaleTimeString()}
                  </div>

                  {request.estimated_response_time && (
                    <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded">
                      <p className="text-sm text-blue-800">
                        Estimated response: {new Date(request.estimated_response_time).toLocaleString()}
                      </p>
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
