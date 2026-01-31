'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiAlertCircle, FiCheck, FiClock, FiMapPin, FiX, FiRefreshCw } from 'react-icons/fi';
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
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  const { accessToken } = useAuthStore();

  const [formData, setFormData] = useState({
    installation_id: '',
    request_type: 'service',
    priority: 'medium',
    description: '',
    preferred_date: '',
  });

  const fetchData = async (showLoading = true) => {
    if (showLoading) setLoading(true);
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
      
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load data. Please try again.');
      console.error('Fetch error:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    if (accessToken) {
      fetchData();
    }
  }, [accessToken]);

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.installation_id) {
      errors.installation_id = 'Please select an installation';
    }

    if (!formData.description || formData.description.trim().length < 10) {
      errors.description = 'Description must be at least 10 characters';
    }

    if (formData.preferred_date && new Date(formData.preferred_date) < new Date()) {
      errors.preferred_date = 'Please select a future date';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (formErrors[field]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

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
        throw new Error(errorData.message || errorData.detail || 'Failed to submit service request');
      }

      setSuccessMessage('Service request submitted successfully! We will contact you soon.');
      setShowForm(false);
      setFormData({
        installation_id: '',
        request_type: 'service',
        priority: 'medium',
        description: '',
        preferred_date: '',
      });

      // Refresh service requests
      await fetchData(false);
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to submit service request. Please try again.');
      console.error('Form submission error:', err);
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
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading service requests...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8 max-w-6xl mx-auto">
      {/* Header */}
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
        {!showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg flex items-center transition-colors"
          >
            <FiTool className="mr-2" />
            New Request
          </button>
        )}
      </div>

      {/* Messages */}
      {successMessage && (
        <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded-lg flex items-start gap-3">
          <FiCheck className="h-5 w-5 shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Success!</p>
            <p className="text-sm">{successMessage}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <FiAlertCircle className="h-5 w-5 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Error</p>
              <p className="text-sm">{error}</p>
            </div>
          </div>
          <button
            onClick={() => fetchData(false)}
            className="text-red-600 hover:text-red-800"
            title="Retry"
          >
            <FiRefreshCw className="h-5 w-5" />
          </button>
        </div>
      )}

      {/* Service Request Form */}
      {showForm && (
        <div className="mb-6 bg-white rounded-lg shadow p-6 border border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Submit Service Request</h2>
            <button
              onClick={() => setShowForm(false)}
              className="text-gray-400 hover:text-gray-600"
              title="Close form"
            >
              <FiX className="h-6 w-6" />
            </button>
          </div>

          {installations.length === 0 && (
            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                No installations found. Please complete your installation setup first.
              </p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Installation Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Installation <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.installation_id}
                onChange={(e) => handleInputChange('installation_id', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 transition ${
                  formErrors.installation_id 
                    ? 'border-red-400 focus:ring-red-500' 
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
              >
                <option value="">Choose an installation...</option>
                {installations.map((installation) => (
                  <option key={installation.id} value={installation.id}>
                    {installation.installation_type} - {installation.system_size} {installation.capacity_unit} ({installation.installation_address})
                  </option>
                ))}
              </select>
              {formErrors.installation_id && (
                <p className="mt-1 text-sm text-red-600">{formErrors.installation_id}</p>
              )}
            </div>

            {/* Request Type and Priority */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Request Type <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.request_type}
                  onChange={(e) => handleInputChange('request_type', e.target.value)}
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
                  Priority <span className="text-red-500">*</span>
                </label>
                <select
                  value={formData.priority}
                  onChange={(e) => handleInputChange('priority', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Low - Non-urgent</option>
                  <option value="medium">Medium - Standard</option>
                  <option value="high">High - Urgent</option>
                  <option value="urgent">Urgent - Critical</option>
                </select>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Please describe the issue or service needed..."
                rows={4}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 transition ${
                  formErrors.description 
                    ? 'border-red-400 focus:ring-red-500' 
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
              />
              <div className="flex items-center justify-between mt-1">
                <p className={`text-sm ${formData.description.length < 10 ? 'text-red-600' : 'text-gray-600'}`}>
                  {formData.description.length} characters (minimum 10)
                </p>
              </div>
              {formErrors.description && (
                <p className="mt-1 text-sm text-red-600">{formErrors.description}</p>
              )}
            </div>

            {/* Preferred Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Service Date
              </label>
              <input
                type="datetime-local"
                value={formData.preferred_date}
                onChange={(e) => handleInputChange('preferred_date', e.target.value)}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 transition ${
                  formErrors.preferred_date 
                    ? 'border-red-400 focus:ring-red-500' 
                    : 'border-gray-300 focus:ring-blue-500'
                }`}
              />
              {formErrors.preferred_date && (
                <p className="mt-1 text-sm text-red-600">{formErrors.preferred_date}</p>
              )}
            </div>

            {/* Form Actions */}
            <div className="flex gap-3 pt-4">
              <button
                type="submit"
                disabled={submitting}
                className={`flex-1 py-2 px-4 rounded-lg font-semibold transition flex items-center justify-center gap-2 ${
                  submitting
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {submitting ? 'Submitting...' : 'Submit Request'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setFormErrors({});
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}
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
