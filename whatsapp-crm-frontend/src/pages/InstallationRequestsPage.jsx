import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminAPI } from '@/services/adminAPI';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  Wrench,
  Search,
  Filter,
  PlayCircle,
  Clock,
  CheckCircle2,
  AlertCircle,
  User,
  MapPin,
  Phone,
  ChevronLeft,
  ChevronRight,
  MessageCircle
} from 'lucide-react';

export default function InstallationRequestsPage() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const [typeFilter, setTypeFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [startingInstallation, setStartingInstallation] = useState(null);
  const pageSize = 10;
  const navigate = useNavigate();

  useEffect(() => {
    loadInstallationRequests();
  }, [statusFilter, typeFilter, currentPage]);

  const loadInstallationRequests = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
      };
      
      if (statusFilter) {
        params.status = statusFilter;
      }
      if (typeFilter) {
        params.installation_type = typeFilter;
      }

      const response = await adminAPI.installationRequests.list(params);
      setRequests(response.data.results || response.data || []);
      setTotalCount(response.data.count || 0);
    } catch (err) {
      console.error('Failed to load installation requests:', err);
      setError('Failed to load installation requests. Please try again.');
      toast.error('Failed to load installation requests');
    } finally {
      setLoading(false);
    }
  };

  const handleStartInstallation = async (requestId) => {
    setStartingInstallation(requestId);
    try {
      const response = await adminAPI.installationRequests.startInstallation(requestId);
      const data = response.data;
      
      toast.success(data.message || 'Installation started successfully');
      
      // Navigate to the installation checklist page
      if (data.installation_system_record_id) {
        navigate(`/installation-checklist/${data.installation_system_record_id}`);
      } else {
        // Reload the list to show updated status
        loadInstallationRequests();
      }
    } catch (err) {
      console.error('Failed to start installation:', err);
      toast.error(err.response?.data?.error || 'Failed to start installation');
    } finally {
      setStartingInstallation(null);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4" />;
      case 'scheduled':
        return <Clock className="w-4 h-4" />;
      case 'in_progress':
        return <AlertCircle className="w-4 h-4" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
      scheduled: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      in_progress: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
      cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const getTypeColor = (type) => {
    const colors = {
      solar: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300',
      starlink: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
      hybrid: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
      custom_furniture: 'bg-teal-100 text-teal-800 dark:bg-teal-900 dark:text-teal-300',
    };
    return colors[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  const filteredRequests = requests.filter((req) => {
    const searchLower = searchTerm.toLowerCase();
    return (
      (req.full_name?.toLowerCase() || '').includes(searchLower) ||
      (req.customer_full_name?.toLowerCase() || '').includes(searchLower) ||
      (req.order_number?.toLowerCase() || '').includes(searchLower) ||
      (req.address?.toLowerCase() || '').includes(searchLower) ||
      (req.contact_phone?.toLowerCase() || '').includes(searchLower)
    );
  });

  const totalPages = Math.ceil(totalCount / pageSize);

  if (loading && requests.length === 0) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-400">Loading installation requests...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Wrench className="w-7 h-7 text-blue-600" />
            Pending Installations
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            View and start pending installation requests
          </p>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative md:col-span-2">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search by name, order, or address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
          </div>

          {/* Status Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          {/* Type Filter */}
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <select
              value={typeFilter}
              onChange={(e) => {
                setTypeFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value="">All Types</option>
              <option value="solar">Solar</option>
              <option value="starlink">Starlink</option>
              <option value="hybrid">Hybrid</option>
              <option value="custom_furniture">Custom Furniture</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={loadInstallationRequests}
            className="mt-2"
          >
            Retry
          </Button>
        </div>
      )}

      {/* Installation Requests Table */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Customer
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Order #
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredRequests.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center">
                    <div className="text-gray-400 dark:text-gray-500">
                      <Wrench className="w-12 h-12 mx-auto mb-2 opacity-50" />
                      <p>No installation requests found</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredRequests.map((req) => (
                  <tr key={req.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <User className="w-4 h-4 text-gray-400 mr-2" />
                        <div>
                          <div className="text-sm font-medium text-gray-900 dark:text-white">
                            {req.customer_full_name || req.full_name || 'N/A'}
                          </div>
                          {req.contact_phone && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                              <Phone className="w-3 h-3" />
                              {req.contact_phone}
                            </div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getTypeColor(req.installation_type)}`}>
                        {req.installation_type_display || req.installation_type?.replace('_', ' ') || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(req.status)}`}>
                        {getStatusIcon(req.status)}
                        {req.status_display || req.status?.replace('_', ' ') || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-900 dark:text-white">
                        {req.order_number || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-start text-sm text-gray-900 dark:text-white max-w-xs truncate">
                        <MapPin className="w-4 h-4 text-gray-400 mr-1 flex-shrink-0 mt-0.5" />
                        <span className="truncate">{req.address || 'N/A'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {req.created_at ? new Date(req.created_at).toLocaleDateString() : 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <div className="flex items-center justify-end gap-2">
                        {/* WhatsApp Button */}
                        {req.contact_phone && (
                          <a
                            href={`https://wa.me/${req.contact_phone.replace(/[^\d]/g, '')}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded bg-green-500 text-white hover:bg-green-600 transition"
                          >
                            <MessageCircle className="w-3 h-3" />
                            Chat
                          </a>
                        )}
                        
                        {/* Start Installing Button - Only show for pending/scheduled requests */}
                        {(req.status === 'pending' || req.status === 'scheduled') && (
                          <Button
                            size="sm"
                            onClick={() => handleStartInstallation(req.id)}
                            disabled={startingInstallation === req.id}
                            className="inline-flex items-center gap-1"
                          >
                            {startingInstallation === req.id ? (
                              <>
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                                Starting...
                              </>
                            ) : (
                              <>
                                <PlayCircle className="w-4 h-4" />
                                Start Installing
                              </>
                            )}
                          </Button>
                        )}
                        
                        {/* View Checklist Button - Only show for in_progress requests */}
                        {req.status === 'in_progress' && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleStartInstallation(req.id)}
                            className="inline-flex items-center gap-1"
                          >
                            <CheckCircle2 className="w-4 h-4" />
                            View Checklist
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              Showing {Math.min((currentPage - 1) * pageSize + 1, totalCount)} to{' '}
              {Math.min(currentPage * pageSize, totalCount)} of {totalCount} requests
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <div className="flex items-center gap-1">
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = i + 1;
                  } else if (currentPage <= 3) {
                    pageNum = i + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i;
                  } else {
                    pageNum = currentPage - 2 + i;
                  }
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-1 rounded-lg ${
                        currentPage === pageNum
                          ? 'bg-blue-600 text-white'
                          : 'border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>
              <button
                onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
