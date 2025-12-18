// Admin Retailers Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import AdminDataTable from '@/components/admin/AdminDataTable';
import AdminFormModal from '@/components/admin/AdminFormModal';
import { adminAPI } from '@/services/adminAPI';

const retailerSchema = z.object({
  company_name: z.string().min(1, 'Company name is required'),
  contact_phone: z.string().optional(),
  contact_email: z.string().email().optional(),
  is_active: z.boolean().optional(),
});

export default function AdminRetailersPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'company_name', label: 'Company Name' },
    { key: 'user_username', label: 'User' },
    { key: 'contact_phone', label: 'Phone' },
    { key: 'contact_email', label: 'Email' },
    { key: 'branch_count', label: 'Branches' },
    {
      key: 'is_active',
      label: 'Active',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
  ];

  const formFields = [
    { name: 'company_name', label: 'Company Name', type: 'text', placeholder: 'Enter company name' },
    { name: 'contact_phone', label: 'Contact Phone', type: 'text', placeholder: '+263...' },
    { name: 'contact_email', label: 'Contact Email', type: 'email', placeholder: 'contact@company.com' },
    { name: 'is_active', label: 'Active', type: 'checkbox' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.retailers.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch retailers');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      if (editingItem) {
        await adminAPI.retailers.update(editingItem.id, formData);
        toast.success('Retailer updated successfully');
      } else {
        await adminAPI.retailers.create(formData);
        toast.success('Retailer created successfully');
      }
      setIsModalOpen(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      toast.error(`Failed to ${editingItem ? 'update' : 'create'} retailer`);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this retailer?')) {
      try {
        await adminAPI.retailers.delete(item.id);
        toast.success('Retailer deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete retailer');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Retailers"
        data={data}
        columns={columns}
        onAdd={() => {
          setEditingItem(null);
          setIsModalOpen(true);
        }}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onSearch={(value) => fetchData({ search: value })}
        isLoading={isLoading}
      />
      <AdminFormModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingItem(null);
        }}
        onSubmit={handleSubmit}
        title={editingItem ? 'Edit Retailer' : 'Create Retailer'}
        fields={formFields}
        defaultValues={editingItem || { is_active: true }}
        schema={retailerSchema}
      />
    </div>
  );
}
