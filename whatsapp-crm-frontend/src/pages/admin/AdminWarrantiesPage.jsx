// Admin Warranties Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';

export default function AdminWarrantiesPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'serialized_item_serial', label: 'Serial Number' },
    { key: 'manufacturer_name', label: 'Manufacturer' },
    { key: 'customer_name', label: 'Customer' },
    {
      key: 'status',
      label: 'Status',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${
          row.status === 'active' ? 'bg-green-100 text-green-800' : 
          row.status === 'expired' ? 'bg-red-100 text-red-800' : 
          'bg-yellow-100 text-yellow-800'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      key: 'start_date',
      label: 'Start Date',
      render: (row) => new Date(row.start_date).toLocaleDateString(),
    },
    {
      key: 'end_date',
      label: 'End Date',
      render: (row) => new Date(row.end_date).toLocaleDateString(),
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.warranties.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch warranties');
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (item) => {
    toast.info(`Edit warranty: ${item.id}`);
    // TODO: Implement edit modal
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this warranty?')) {
      try {
        await adminAPI.warranties.delete(item.id);
        toast.success('Warranty deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete warranty');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Warranties"
        data={data}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onSearch={(value) => fetchData({ search: value })}
        isLoading={isLoading}
      />
    </div>
  );
}
