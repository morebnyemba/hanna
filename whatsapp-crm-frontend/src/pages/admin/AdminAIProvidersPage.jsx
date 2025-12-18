// Admin AI Providers Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import AdminDataTable from '@/components/admin/AdminDataTable';
import AdminFormModal from '@/components/admin/AdminFormModal';
import { adminAPI } from '@/services/adminAPI';

const aiProviderSchema = z.object({
  provider: z.string().min(1, 'Provider name is required'),
  is_active: z.boolean().optional(),
});

export default function AdminAIProvidersPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'provider', label: 'Provider' },
    {
      key: 'is_active',
      label: 'Active',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'updated_at',
      label: 'Updated',
      render: (row) => new Date(row.updated_at).toLocaleString(),
    },
  ];

  const formFields = [
    {
      name: 'provider',
      label: 'Provider',
      type: 'select',
      options: [
        { value: 'openai', label: 'OpenAI' },
        { value: 'anthropic', label: 'Anthropic' },
        { value: 'google', label: 'Google' },
      ],
    },
    { name: 'is_active', label: 'Active', type: 'checkbox' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.aiProviders.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch AI providers');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      if (editingItem) {
        await adminAPI.aiProviders.update(editingItem.id, formData);
        toast.success('AI Provider updated successfully');
      } else {
        await adminAPI.aiProviders.create(formData);
        toast.success('AI Provider created successfully');
      }
      setIsModalOpen(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      toast.error(`Failed to ${editingItem ? 'update' : 'create'} AI provider`);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this AI provider?')) {
      try {
        await adminAPI.aiProviders.delete(item.id);
        toast.success('AI Provider deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete AI provider');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="AI Providers"
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
        title={editingItem ? 'Edit AI Provider' : 'Create AI Provider'}
        fields={formFields}
        defaultValues={editingItem || { is_active: true }}
        schema={aiProviderSchema}
      />
    </div>
  );
}
