'use client';

import { useState, useEffect } from 'react';
import { FiBell, FiSearch, FiChevronLeft, FiChevronRight, FiRefreshCw, FiFilter, FiFileText } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';

interface Notification {
  id: number;
  recipient: {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
  };
  channel: string;
  status: 'pending' | 'sent' | 'failed' | 'read';
  content: string;
  template_name: string | null;
  created_at: string;
  sent_at: string | null;
  error_message: string | null;
}

interface NotificationTemplate {
  id: number;
  name: string;
  description: string | null;
  message_body: string;
  sync_status: string;
  created_at: string;
  updated_at: string;
}

const StatusBadge = ({ status }: { status: Notification['status'] }) => {
  const colors = {
    pending: 'bg-yellow-100 text-yellow-800',
    sent: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    read: 'bg-blue-100 text-blue-800',
  };

  return (
    <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-full"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-20"></div>
    </td>
  </tr>
);

export default function AdminNotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [filteredNotifications, setFilteredNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTab, setActiveTab] = useState<'notifications' | 'templates'>('notifications');
  const itemsPerPage = 10;

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get('/crm-api/admin-panel/notifications/');
      setNotifications(response.data.results || response.data);
      setFilteredNotifications(response.data.results || response.data);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch notifications.';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await apiClient.get('/crm-api/admin-panel/notification-templates/');
      setTemplates(response.data.results || response.data);
    } catch (err: unknown) {
      console.error('Failed to fetch templates:', err);
    }
  };

  useEffect(() => {
    fetchNotifications();
    fetchTemplates();
  }, []);

  // Filter notifications based on search and status
  useEffect(() => {
    let filtered = notifications;

    if (searchTerm.trim() !== '') {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(notification => {
        const recipientName = `${notification.recipient?.first_name || ''} ${notification.recipient?.last_name || ''}`.toLowerCase();
        const recipientEmail = notification.recipient?.email?.toLowerCase() || '';
        const content = notification.content?.toLowerCase() || '';
        const templateName = notification.template_name?.toLowerCase() || '';
        return recipientName.includes(search) || recipientEmail.includes(search) || content.includes(search) || templateName.includes(search);
      });
    }

    if (statusFilter !== 'all') {
      filtered = filtered.filter(n => n.status === statusFilter);
    }

    setFilteredNotifications(filtered);
    setCurrentPage(1);
  }, [searchTerm, statusFilter, notifications]);

  // Pagination
  const totalPages = Math.ceil(filteredNotifications.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentNotifications = filteredNotifications.slice(startIndex, endIndex);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  // Stats
  const stats = {
    total: notifications.length,
    pending: notifications.filter(n => n.status === 'pending').length,
    sent: notifications.filter(n => n.status === 'sent').length,
    failed: notifications.filter(n => n.status === 'failed').length,
  };

  return (
    <>
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiBell className="mr-3" />
          Notifications
        </h1>
        <button
          onClick={() => {
            fetchNotifications();
            fetchTemplates();
          }}
          className="flex items-center justify-center px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition"
        >
          <FiRefreshCw className="mr-2" />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">Total</div>
          <div className="text-2xl font-bold text-gray-900">{stats.total}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">Pending</div>
          <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">Sent</div>
          <div className="text-2xl font-bold text-green-600">{stats.sent}</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-sm text-gray-500">Failed</div>
          <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-4 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('notifications')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'notifications'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FiBell className="inline mr-2" />
            Notifications ({notifications.length})
          </button>
          <button
            onClick={() => setActiveTab('templates')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'templates'
                ? 'border-purple-500 text-purple-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <FiFileText className="inline mr-2" />
            Templates ({templates.length})
          </button>
        </nav>
      </div>

      {activeTab === 'notifications' && (
        <>
          {/* Search and Filter Bar */}
          <div className="mb-4 flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search by recipient, content, or template..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              />
            </div>
            <div className="relative">
              <FiFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent appearance-none bg-white"
              >
                <option value="all">All Status</option>
                <option value="pending">Pending</option>
                <option value="sent">Sent</option>
                <option value="failed">Failed</option>
                <option value="read">Read</option>
              </select>
            </div>
          </div>

          {error && <p className="text-red-500 mb-4">Error: {error}</p>}

          <div className="bg-white p-3 sm:p-6 rounded-lg shadow-md border border-gray-200">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Recipient</th>
                    <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template</th>
                    <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                    <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sent</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {loading ? (
                    <>
                      <SkeletonRow />
                      <SkeletonRow />
                      <SkeletonRow />
                      <SkeletonRow />
                      <SkeletonRow />
                    </>
                  ) : currentNotifications.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 sm:px-6 text-center text-gray-500">
                        {searchTerm || statusFilter !== 'all' ? 'No notifications found matching your filters' : 'No notifications found'}
                      </td>
                    </tr>
                  ) : (
                    currentNotifications.map((notification) => (
                      <tr key={notification.id} className="hover:bg-gray-50 transition-colors duration-150">
                        <td className="px-4 py-3 sm:px-6 sm:py-4">
                          <div className="text-sm font-medium text-gray-900">
                            {notification.recipient?.first_name} {notification.recipient?.last_name}
                          </div>
                          <div className="text-xs text-gray-500">
                            {notification.recipient?.email}
                          </div>
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                          <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                            {notification.template_name || '-'}
                          </span>
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-4">
                          <StatusBadge status={notification.status} />
                          {notification.status === 'failed' && notification.error_message && (
                            <div className="mt-1 text-xs text-red-500 max-w-xs truncate" title={notification.error_message}>
                              {notification.error_message}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                          {formatDate(notification.created_at)}
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                          {formatDate(notification.sent_at)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {!loading && totalPages > 1 && (
              <div className="mt-4 flex flex-col sm:flex-row items-center justify-between border-t border-gray-200 pt-4 gap-3">
                <div className="text-xs sm:text-sm text-gray-700">
                  Showing {startIndex + 1} to {Math.min(endIndex, filteredNotifications.length)} of {filteredNotifications.length} notifications
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                    disabled={currentPage === 1}
                    className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <FiChevronLeft />
                  </button>
                  <span className="px-3 py-1 text-xs sm:text-sm">
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                    disabled={currentPage === totalPages}
                    className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <FiChevronRight />
                  </button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'templates' && (
        <div className="bg-white p-3 sm:p-6 rounded-lg shadow-md border border-gray-200">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Template Name</th>
                  <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
                  <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sync Status</th>
                  <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {templates.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 sm:px-6 text-center text-gray-500">
                      No templates found. Run the management command to load default templates.
                    </td>
                  </tr>
                ) : (
                  templates.map((template) => (
                    <tr key={template.id} className="hover:bg-gray-50 transition-colors duration-150">
                      <td className="px-4 py-3 sm:px-6 sm:py-4">
                        <span className="font-mono text-sm font-medium text-gray-900">
                          {template.name}
                        </span>
                      </td>
                      <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500 max-w-md truncate">
                        {template.description || '-'}
                      </td>
                      <td className="px-4 py-3 sm:px-6 sm:py-4">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          template.sync_status === 'synced' ? 'bg-green-100 text-green-800' :
                          template.sync_status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          template.sync_status === 'failed' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {template.sync_status}
                        </span>
                      </td>
                      <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                        {formatDate(template.updated_at)}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
