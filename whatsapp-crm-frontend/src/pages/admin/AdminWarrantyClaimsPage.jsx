// Admin Warranty Claims Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';

export default function AdminWarrantyClaimsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'claim_id', label: 'Claim ID' },
    { key: 'warranty_item', label: 'Item' },
    {
      key: 'status',
      label: 'Status',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${
          row.status === 'approved' ? 'bg-green-100 text-green-800' : 
          row.status === 'rejected' ? 'bg-red-100 text-red-800' : 
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'created_at',
      label: 'Created',
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
  ];

  const filters = [
    {
      key: 'status',
      label: 'Status',
      options: [
        { value: 'pending', label: 'Pending' },
        { value: 'approved', label: 'Approved' },
        { value: 'rejected', label: 'Rejected' },
      ],
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.warrantyClaims.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch warranty claims');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (item) => {
    toast.info(`Edit warranty claim: ${item.claim_id}`);
    // TODO: Implement edit modal
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this warranty claim?')) {
      try {
        await adminAPI.warrantyClaims.delete(item.id);
        toast.success('Warranty claim deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete warranty claim');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Warranty Claims"
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
