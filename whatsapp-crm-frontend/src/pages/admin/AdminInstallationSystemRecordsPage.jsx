// Admin Installation System Records Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';
import { DownloadInstallationReportButton } from '@/components/DownloadButtons';

export default function AdminInstallationSystemRecordsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

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
        <span className={`px-2 py-1 rounded text-xs ${
          row.installation_status === 'commissioned' || row.installation_status === 'active' 
            ? 'bg-green-100 text-green-800' : 
          row.installation_status === 'in_progress' 
            ? 'bg-blue-100 text-blue-800' : 
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.installation_status?.replace('_', ' ') || 'N/A'}
        </span>
      ),
    },
    {
      key: 'system_size',
      label: 'System Size',
      render: (row) => row.system_size ? `${row.system_size} ${row.capacity_unit || ''}` : 'N/A',
    },
    {
      key: 'installation_date',
      label: 'Installation Date',
      render: (row) => row.installation_date ? new Date(row.installation_date).toLocaleDateString() : 'N/A',
    },
    {
      key: 'commissioning_date',
      label: 'Commissioning Date',
      render: (row) => row.commissioning_date ? new Date(row.commissioning_date).toLocaleDateString() : 'N/A',
    },
    {
      key: 'actions',
      label: 'Report',
      render: (row) => (
        <DownloadInstallationReportButton 
          installationId={row.id} 
          variant="icon"
          isAdmin={true}
        />
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
    toast.info(`Edit installation: ${item.id?.slice(0, 8)}`);
    // TODO: Implement edit modal
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

  return (
    <div className="container mx-auto p-6">
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
    </div>
  );
}
