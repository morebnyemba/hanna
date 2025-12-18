// Admin Carts Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';

export default function AdminCartsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'contact_name', label: 'Contact' },
    { key: 'items_count', label: 'Items' },
    {
      key: 'created_at',
      label: 'Created',
      render: (row) => new Date(row.created_at).toLocaleString(),
    },
    {
      key: 'updated_at',
      label: 'Updated',
      render: (row) => new Date(row.updated_at).toLocaleString(),
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.carts.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch carts');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this cart?')) {
      try {
        await adminAPI.carts.delete(item.id);
        toast.success('Cart deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete cart');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Shopping Carts"
        data={data}
        columns={columns}
        onDelete={handleDelete}
        onSearch={(value) => fetchData({ search: value })}
        isLoading={isLoading}
      />
    </div>
  );
}
