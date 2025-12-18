// Admin Notifications Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import AdminDataTable from '@/components/admin/AdminDataTable';
import AdminFormModal from '@/components/admin/AdminFormModal';
import { adminAPI } from '@/services/adminAPI';

const notificationSchema = z.object({
  recipient: z.string().min(1, 'Recipient is required'),
  channel: z.string().min(1, 'Channel is required'),
  status: z.string().optional(),
});

export default function AdminNotificationsPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'recipient_name', label: 'Recipient' },
    { key: 'channel', label: 'Channel' },
    {
      key: 'status',
      label: 'Status',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${
          row.status === 'sent' ? 'bg-green-100 text-green-800' : 
          row.status === 'failed' ? 'bg-red-100 text-red-800' : 
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

  const formFields = [
    { name: 'recipient', label: 'Recipient ID', type: 'number', placeholder: 'User ID' },
    {
      name: 'channel',
      label: 'Channel',
      type: 'select',
      options: [
        { value: 'email', label: 'Email' },
        { value: 'sms', label: 'SMS' },
        { value: 'whatsapp', label: 'WhatsApp' },
      ],
    },
    {
      name: 'status',
      label: 'Status',
      type: 'select',
      options: [
        { value: 'pending', label: 'Pending' },
        { value: 'sent', label: 'Sent' },
        { value: 'failed', label: 'Failed' },
      ],
    },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.notifications.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch notifications');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      if (editingItem) {
        await adminAPI.notifications.update(editingItem.id, formData);
        toast.success('Notification updated successfully');
      } else {
        await adminAPI.notifications.create(formData);
        toast.success('Notification created successfully');
      }
      setIsModalOpen(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      toast.error(`Failed to ${editingItem ? 'update' : 'create'} notification`);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this notification?')) {
      try {
        await adminAPI.notifications.delete(item.id);
        toast.success('Notification deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete notification');
      }
    }
  };

  const handleAdd = () => {
    setEditingItem(null);
    setIsModalOpen(true);
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Notifications"
        data={data}
        columns={columns}
        onAdd={handleAdd}
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
        title={editingItem ? 'Edit Notification' : 'Create Notification'}
        fields={formFields}
        defaultValues={editingItem || {}}
        schema={notificationSchema}
      />
    </div>
  );
}
