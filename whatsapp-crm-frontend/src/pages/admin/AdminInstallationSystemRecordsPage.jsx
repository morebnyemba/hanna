// Admin Installation System Records Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';
import { DownloadInstallationReportButton } from '@/components/DownloadButtons';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { FiX } from 'react-icons/fi';

export default function AdminInstallationSystemRecordsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [showDetail, setShowDetail] = useState(false);

  const columns = [
    { key: 'id', label: 'ID', render: (row) => row.id?.slice(0, 8) || 'N/A' },
    { key: 'customer_name', label: 'Customer' },
    { 
      key: 'installation_type', 
      label: 'Type',
      render: (row) => row.installation_type?.replace('_', ' ').toUpperCase() || 'N/A'
    },
    {
      key: 'installation_status',
      label: 'Status',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          row.installation_status === 'commissioned' || row.installation_status === 'active' 
            ? 'bg-green-100 text-green-800' : 
          row.installation_status === 'in_progress' 
            ? 'bg-blue-100 text-blue-800' : 
          row.installation_status === 'pending'
            ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-800'
        }`}>
          {row.installation_status?.replace('_', ' ').toUpperCase() || 'N/A'}
        </span>
      ),
    },
    {
      key: 'system_size',
      label: 'System Size',
      render: (row) => row.system_size ? `${row.system_size} ${row.capacity_unit || 'kW'}` : 'N/A',
    },
    {
      key: 'installation_date',
      label: 'Installation Date',
      render: (row) => row.installation_date ? new Date(row.installation_date).toLocaleDateString() : 'N/A',
    },
    {
      key: 'commissioning_date',
      label: 'Commissioned',
      render: (row) => row.commissioning_date ? new Date(row.commissioning_date).toLocaleDateString() : 'Pending',
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (row) => (
        <div className="flex gap-2">
          <button
            onClick={() => {
              setSelectedRecord(row);
              setShowDetail(true);
            }}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View
          </button>
          <DownloadInstallationReportButton 
            installationId={row.id} 
            variant="icon"
            isAdmin={true}
          />
        </div>
      ),
    },
  ];

  const filters = [
    {
      key: 'installation_type',
      label: 'Type',
      options: [
        { value: 'solar', label: 'Solar' },
        { value: 'starlink', label: 'Starlink' },
        { value: 'hybrid', label: 'Hybrid' },
        { value: 'custom_furniture', label: 'Custom Furniture' },
      ],
    },
    {
      key: 'installation_status',
      label: 'Status',
      options: [
        { value: 'pending', label: 'Pending' },
        { value: 'in_progress', label: 'In Progress' },
        { value: 'commissioned', label: 'Commissioned' },
        { value: 'active', label: 'Active' },
        { value: 'decommissioned', label: 'Decommissioned' },
      ],
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      // Note: This endpoint might need to be added to adminAPI if not already present
      const response = await adminAPI.installationSystemRecords?.list(params) || 
                       { data: [] }; // Fallback if not implemented
      setData(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to fetch installation system records:', error);
      toast.error('Failed to fetch installation system records');
      setData([]); // Set empty array on error
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (item) => {
    setSelectedRecord(item);
    setShowDetail(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this installation system record?')) {
      try {
        await adminAPI.installationSystemRecords.delete(item.id);
        toast.success('Installation system record deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete installation system record');
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'commissioned':
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'in_progress':
        return 'bg-blue-100 text-blue-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Calculate stats
  const stats = {
    total: data.length,
    commissioned: data.filter(r => r.installation_status === 'commissioned' || r.installation_status === 'active').length,
    inProgress: data.filter(r => r.installation_status === 'in_progress').length,
    pending: data.filter(r => r.installation_status === 'pending').length,
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <p className="text-gray-500 text-sm font-medium">Total Installations</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{stats.total}</p>
        </div>
        <div className="bg-green-50 rounded-lg shadow p-6 border-l-4 border-green-500">
          <p className="text-green-700 text-sm font-medium">Commissioned</p>
          <p className="text-3xl font-bold text-green-600 mt-2">{stats.commissioned}</p>
        </div>
        <div className="bg-blue-50 rounded-lg shadow p-6 border-l-4 border-blue-500">
          <p className="text-blue-700 text-sm font-medium">In Progress</p>
          <p className="text-3xl font-bold text-blue-600 mt-2">{stats.inProgress}</p>
        </div>
        <div className="bg-yellow-50 rounded-lg shadow p-6 border-l-4 border-yellow-500">
          <p className="text-yellow-700 text-sm font-medium">Pending</p>
          <p className="text-3xl font-bold text-yellow-600 mt-2">{stats.pending}</p>
        </div>
      </div>

      {/* Data Table */}
      <AdminDataTable
        title="Installation System Records"
        data={data}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onSearch={(value) => fetchData({ search: value })}
        filters={filters}
        isLoading={isLoading}
      />

      {/* Detail Modal */}
      <Dialog open={showDetail} onOpenChange={setShowDetail}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>Installation Details</span>
              <Badge className={getStatusColor(selectedRecord?.installation_status)}>
                {selectedRecord?.installation_status?.replace('_', ' ').toUpperCase()}
              </Badge>
            </DialogTitle>
            <DialogDescription>
              ID: {selectedRecord?.id?.slice(0, 16)}...
            </DialogDescription>
          </DialogHeader>

          {selectedRecord && (
            <div className="space-y-6">
              {/* Customer Information */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Customer Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Name</p>
                    <p className="font-medium">{selectedRecord.customer_name || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Phone</p>
                    <p className="font-medium">{selectedRecord.customer_phone || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Email</p>
                    <p className="font-medium text-sm">{selectedRecord.customer_email || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Address</p>
                    <p className="font-medium text-sm">{selectedRecord.installation_address || 'N/A'}</p>
                  </div>
                </div>
              </div>

              {/* Installation Details */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Installation Details</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Type</p>
                    <p className="font-medium">{selectedRecord.installation_type?.replace('_', ' ').toUpperCase()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">System Size</p>
                    <p className="font-medium">{selectedRecord.system_size} {selectedRecord.capacity_unit || 'kW'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Installation Date</p>
                    <p className="font-medium">
                      {selectedRecord.installation_date 
                        ? new Date(selectedRecord.installation_date).toLocaleDateString() 
                        : 'Pending'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Commissioning Date</p>
                    <p className="font-medium">
                      {selectedRecord.commissioning_date 
                        ? new Date(selectedRecord.commissioning_date).toLocaleDateString() 
                        : 'Pending'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Additional Details */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Additional Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Assigned Technician</p>
                    <p className="font-medium">{selectedRecord.assigned_technician_name || 'Unassigned'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Warranty Years</p>
                    <p className="font-medium">{selectedRecord.warranty_years || 'N/A'} years</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Location (Lat/Long)</p>
                    <p className="font-medium text-sm">
                      {selectedRecord.location_latitude && selectedRecord.location_longitude 
                        ? `${selectedRecord.location_latitude.toFixed(4)}, ${selectedRecord.location_longitude.toFixed(4)}`
                        : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Notes</p>
                    <p className="font-medium text-sm">{selectedRecord.notes || 'No notes'}</p>
                  </div>
                </div>
              </div>

              {/* Checklist Status */}
              {selectedRecord.checklist_completion_percentage !== undefined && (
                <div>
                  <h3 className="text-lg font-semibold mb-3">Checklist Progress</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Completion Status</span>
                      <span className="font-bold text-lg">{selectedRecord.checklist_completion_percentage}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all"
                        style={{ width: `${selectedRecord.checklist_completion_percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* Created/Updated Timestamps */}
              <div className="border-t pt-4">
                <div className="grid grid-cols-2 gap-4 text-xs text-gray-500">
                  <div>
                    <p>Created</p>
                    <p className="text-gray-700">
                      {selectedRecord.created_at 
                        ? new Date(selectedRecord.created_at).toLocaleString() 
                        : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p>Last Updated</p>
                    <p className="text-gray-700">
                      {selectedRecord.updated_at 
                        ? new Date(selectedRecord.updated_at).toLocaleString() 
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
