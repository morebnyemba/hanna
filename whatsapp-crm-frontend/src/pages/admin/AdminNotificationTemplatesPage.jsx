// Admin Notification Templates Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import AdminDataTable from '@/components/admin/AdminDataTable';
import AdminFormModal from '@/components/admin/AdminFormModal';
import { adminAPI } from '@/services/adminAPI';

const templateSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
});

export default function AdminNotificationTemplatesPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'name', label: 'Name' },
    { key: 'description', label: 'Description' },
    {
      key: 'updated_at',
      label: 'Updated',
      render: (row) => new Date(row.updated_at).toLocaleString(),
    },
  ];

  const formFields = [
    { name: 'name', label: 'Template Name', type: 'text', placeholder: 'Enter template name' },
    { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Enter description' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.notificationTemplates.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch templates');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      if (editingItem) {
        await adminAPI.notificationTemplates.update(editingItem.id, formData);
        toast.success('Template updated successfully');
      } else {
        await adminAPI.notificationTemplates.create(formData);
        toast.success('Template created successfully');
      }
      setIsModalOpen(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      toast.error(`Failed to ${editingItem ? 'update' : 'create'} template`);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this template?')) {
      try {
        await adminAPI.notificationTemplates.delete(item.id);
        toast.success('Template deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete template');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Notification Templates"
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
        title={editingItem ? 'Edit Template' : 'Create Template'}
        fields={formFields}
        defaultValues={editingItem || {}}
        schema={templateSchema}
      />
    </div>
  );
}
