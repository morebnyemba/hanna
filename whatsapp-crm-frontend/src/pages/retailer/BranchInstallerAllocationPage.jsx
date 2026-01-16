// src/pages/retailer/BranchInstallerAllocationPage.jsx
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import {
  Users,
  Calendar,
  Plus,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  User,
  MapPin,
  Wrench,
  Eye,
  X
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const BranchInstallerAllocationPage = () => {
  const [installations, setInstallations] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [installers, setInstallers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedInstallation, setSelectedInstallation] = useState(null);
  const [selectedInstaller, setSelectedInstaller] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [scheduledStartTime, setScheduledStartTime] = useState('');
  const [scheduledEndTime, setScheduledEndTime] = useState('');
  const [estimatedDuration, setEstimatedDuration] = useState('');
  const [notes, setNotes] = useState('');

  useEffect(() => {
    loadData();
  }, [statusFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('access_token');
      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      // Load assignments
      const assignmentsRes = await fetch(
        `${API_BASE}/crm-api/branch/installer-assignments/${statusFilter ? `?status=${statusFilter}` : ''}`,
        { headers }
      );
      if (assignmentsRes.ok) {
        const assignmentsData = await assignmentsRes.json();
        setAssignments(assignmentsData.results || assignmentsData);
      }

      // Load installations
      const installationsRes = await fetch(
        `${API_BASE}/crm-api/retailer/installations/?installation_status=pending,in_progress`,
        { headers }
      );
      if (installationsRes.ok) {
        const installationsData = await installationsRes.json();
        setInstallations(installationsData.results || installationsData);
      }

      // Load installers
      const installersRes = await fetch(
        `${API_BASE}/crm-api/branch/installers/`,
        { headers }
      );
      if (installersRes.ok) {
        const installersData = await installersRes.json();
        setInstallers(installersData.results || installersData);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const openAssignModal = (installation) => {
    setSelectedInstallation(installation);
    setShowAssignModal(true);
    setSelectedInstaller('');
    setScheduledDate('');
    setScheduledStartTime('');
    setScheduledEndTime('');
    setEstimatedDuration('');
    setNotes('');
  };

  const closeAssignModal = () => {
    setShowAssignModal(false);
    setSelectedInstallation(null);
  };

  const handleAssignInstaller = async (e) => {
    e.preventDefault();
    
    if (!selectedInstaller || !scheduledDate) {
      toast.error('Please select installer and date');
      return;
    }

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch(
        `${API_BASE}/crm-api/branch/installer-assignments/`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            installation_record: selectedInstallation.id,
            installer: selectedInstaller,
            scheduled_date: scheduledDate,
            scheduled_start_time: scheduledStartTime || null,
            scheduled_end_time: scheduledEndTime || null,
            estimated_duration_hours: estimatedDuration || null,
            notes: notes,
          }),
        }
      );

      if (response.ok) {
        toast.success('Installer assigned successfully');
        closeAssignModal();
        loadData();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to assign installer');
      }
    } catch (err) {
      console.error('Error assigning installer:', err);
      toast.error('Failed to assign installer');
    }
  };

  const filteredAssignments = assignments.filter((assignment) => {
    const searchLower = searchTerm.toLowerCase();
    return (
      (assignment.installation_details?.customer_name?.toLowerCase() || '').includes(searchLower) ||
      (assignment.installer_details?.name?.toLowerCase() || '').includes(searchLower) ||
      (assignment.installation_details?.installation_address?.toLowerCase() || '').includes(searchLower)
    );
  });

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      completed: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'in_progress':
        return <Clock className="w-4 h-4" />;
      case 'cancelled':
        return <X className="w-4 h-4" />;
      default:
        return <AlertCircle className="w-4 h-4" />;
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading assignments...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Users className="w-8 h-8 text-blue-600" />
          Installer Allocation
        </h1>
        <p className="text-gray-600 mt-1">
          Assign installers to pending installations and track progress
        </p>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search assignments..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none"
            >
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>
      </div>

      {/* Pending Installations */}
      {installations.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-orange-500" />
            Pending Installations ({installations.length})
          </h2>
          <div className="space-y-3">
            {installations.map((installation) => (
              <div
                key={installation.id}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Wrench className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="font-medium text-gray-900">
                        {installation.customer_name}
                      </p>
                      <p className="text-sm text-gray-600">
                        {installation.installation_type_display} - {installation.short_id}
                      </p>
                      <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                        <MapPin className="w-4 h-4" />
                        {installation.installation_address}
                      </p>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => openAssignModal(installation)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Assign Installer
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Current Assignments */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Current Assignments ({filteredAssignments.length})
        </h2>
        
        {filteredAssignments.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500">No assignments found</p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredAssignments.map((assignment) => (
              <div
                key={assignment.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(assignment.status)}`}>
                        {getStatusIcon(assignment.status)}
                        {assignment.status_display}
                      </span>
                      {assignment.is_overdue && (
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          <AlertCircle className="w-3 h-3" />
                          Overdue
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Installation</p>
                        <p className="font-medium text-gray-900">
                          {assignment.installation_details?.customer_name}
                        </p>
                        <p className="text-sm text-gray-600">
                          {assignment.installation_details?.installation_type_display}
                        </p>
                        <p className="text-sm text-gray-500 flex items-center gap-1 mt-1">
                          <MapPin className="w-4 h-4" />
                          {assignment.installation_details?.installation_address}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Installer</p>
                        <p className="font-medium text-gray-900 flex items-center gap-2">
                          <User className="w-4 h-4 text-gray-400" />
                          {assignment.installer_details?.name}
                        </p>
                        <p className="text-sm text-gray-600">
                          {assignment.installer_details?.specialization || 'General'}
                        </p>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-500 mb-1">Schedule</p>
                        <p className="font-medium text-gray-900 flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          {new Date(assignment.scheduled_date).toLocaleDateString()}
                        </p>
                        {assignment.scheduled_start_time && (
                          <p className="text-sm text-gray-600">
                            {assignment.scheduled_start_time} - {assignment.scheduled_end_time}
                          </p>
                        )}
                      </div>
                      
                      {assignment.customer_satisfaction_rating && (
                        <div>
                          <p className="text-sm text-gray-500 mb-1">Customer Rating</p>
                          <div className="flex items-center gap-1">
                            {[...Array(5)].map((_, i) => (
                              <span
                                key={i}
                                className={`text-lg ${
                                  i < assignment.customer_satisfaction_rating
                                    ? 'text-yellow-400'
                                    : 'text-gray-300'
                                }`}
                              >
                                ★
                              </span>
                            ))}
                            <span className="text-sm text-gray-600 ml-2">
                              ({assignment.customer_satisfaction_rating}/5)
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Assign Installer Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-gray-900">
                  Assign Installer
                </h2>
                <button
                  onClick={closeAssignModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              {selectedInstallation && (
                <div className="bg-gray-50 rounded-lg p-4 mb-6">
                  <p className="text-sm text-gray-500 mb-1">Installation</p>
                  <p className="font-medium text-gray-900">
                    {selectedInstallation.customer_name}
                  </p>
                  <p className="text-sm text-gray-600">
                    {selectedInstallation.installation_type_display}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    {selectedInstallation.installation_address}
                  </p>
                </div>
              )}

              <form onSubmit={handleAssignInstaller} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Select Installer *
                  </label>
                  <select
                    value={selectedInstaller}
                    onChange={(e) => setSelectedInstaller(e.target.value)}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">-- Choose Installer --</option>
                    {installers.map((installer) => (
                      <option key={installer.id} value={installer.id}>
                        {installer.name} {installer.specialization && `(${installer.specialization})`}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Scheduled Date *
                  </label>
                  <input
                    type="date"
                    value={scheduledDate}
                    onChange={(e) => setScheduledDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    required
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Start Time
                    </label>
                    <input
                      type="time"
                      value={scheduledStartTime}
                      onChange={(e) => setScheduledStartTime(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      End Time
                    </label>
                    <input
                      type="time"
                      value={scheduledEndTime}
                      onChange={(e) => setScheduledEndTime(e.target.value)}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Estimated Duration (hours)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={estimatedDuration}
                    onChange={(e) => setEstimatedDuration(e.target.value)}
                    placeholder="e.g., 4.5"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Notes
                  </label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={3}
                    placeholder="Any additional notes or instructions..."
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={closeAssignModal}
                    className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Assign Installer
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BranchInstallerAllocationPage;
