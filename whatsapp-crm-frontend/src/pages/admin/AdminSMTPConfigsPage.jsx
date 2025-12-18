// Admin SMTP Configs Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import AdminDataTable from '@/components/admin/AdminDataTable';
import AdminFormModal from '@/components/admin/AdminFormModal';
import { adminAPI } from '@/services/adminAPI';

const smtpSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  host: z.string().min(1, 'Host is required'),
  port: z.number().min(1, 'Port is required'),
  username: z.string().min(1, 'Username is required'),
  password: z.string().optional(),
  use_tls: z.boolean().optional(),
  use_ssl: z.boolean().optional(),
  is_active: z.boolean().optional(),
});

export default function AdminSMTPConfigsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name' },
    { key: 'host', label: 'Host' },
    { key: 'port', label: 'Port' },
    { key: 'username', label: 'Username' },
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
    { name: 'name', label: 'Config Name', type: 'text', placeholder: 'My SMTP Config' },
    { name: 'host', label: 'SMTP Host', type: 'text', placeholder: 'smtp.gmail.com' },
    { name: 'port', label: 'Port', type: 'number', placeholder: '587' },
    { name: 'username', label: 'Username', type: 'text', placeholder: 'user@example.com' },
    { name: 'password', label: 'Password', type: 'password', placeholder: '••••••••' },
    { name: 'use_tls', label: 'Use TLS', type: 'checkbox' },
    { name: 'use_ssl', label: 'Use SSL', type: 'checkbox' },
    { name: 'is_active', label: 'Active', type: 'checkbox' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.smtpConfigs.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch SMTP configs');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      if (editingItem) {
        await adminAPI.smtpConfigs.update(editingItem.id, formData);
        toast.success('SMTP Config updated successfully');
      } else {
        await adminAPI.smtpConfigs.create(formData);
        toast.success('SMTP Config created successfully');
      }
      setIsModalOpen(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      toast.error(`Failed to ${editingItem ? 'update' : 'create'} SMTP config`);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this SMTP config?')) {
      try {
        await adminAPI.smtpConfigs.delete(item.id);
        toast.success('SMTP Config deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete SMTP config');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="SMTP Configurations"
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
        title={editingItem ? 'Edit SMTP Config' : 'Create SMTP Config'}
        fields={formFields}
        defaultValues={editingItem || { use_tls: true, is_active: true }}
        schema={smtpSchema}
      />
    </div>
  );
}
