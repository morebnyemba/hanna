// Admin Technicians Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { z } from 'zod';
import AdminDataTable from '@/components/admin/AdminDataTable';
import AdminFormModal from '@/components/admin/AdminFormModal';
import { adminAPI } from '@/services/adminAPI';

const technicianSchema = z.object({
  specialization: z.string().optional(),
  contact_phone: z.string().optional(),
});

export default function AdminTechniciansPage() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'user_username', label: 'User' },
    { key: 'specialization', label: 'Specialization' },
    { key: 'contact_phone', label: 'Phone' },
  ];

  const formFields = [
    { name: 'specialization', label: 'Specialization', type: 'text', placeholder: 'e.g., Solar Panels' },
    { name: 'contact_phone', label: 'Contact Phone', type: 'text', placeholder: '+263...' },
  ];

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.technicians.list(params);
      setData(response.data.results || response.data);
    } catch (error) {
      toast.error('Failed to fetch technicians');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    try {
      if (editingItem) {
        await adminAPI.technicians.update(editingItem.id, formData);
        toast.success('Technician updated successfully');
      } else {
        await adminAPI.technicians.create(formData);
        toast.success('Technician created successfully');
      }
      setIsModalOpen(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      toast.error(`Failed to ${editingItem ? 'update' : 'create'} technician`);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDelete = async (item) => {
    if (window.confirm('Are you sure you want to delete this technician?')) {
      try {
        await adminAPI.technicians.delete(item.id);
        toast.success('Technician deleted successfully');
        fetchData();
      } catch (error) {
        toast.error('Failed to delete technician');
      }
    }
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="Technicians"
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
        title={editingItem ? 'Edit Technician' : 'Create Technician'}
        fields={formFields}
        defaultValues={editingItem || {}}
        schema={technicianSchema}
      />
    </div>
  );
}
