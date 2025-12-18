// Admin Users Management Page
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';
import AdminDataTable from '@/components/admin/AdminDataTable';
import { adminAPI } from '@/services/adminAPI';

export default function AdminUsersPage() {
  const [users, setUsers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'username', label: 'Username' },
    { key: 'email', label: 'Email' },
    {
      key: 'full_name',
      label: 'Full Name',
      render: (row) => `${row.first_name} ${row.last_name}`.trim() || '-',
    },
    {
      key: 'is_active',
      label: 'Active',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${row.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      ),
    },
    {
      key: 'is_staff',
      label: 'Staff',
      render: (row) => (
        <span className={`px-2 py-1 rounded text-xs ${row.is_staff ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}`}>
          {row.is_staff ? 'Yes' : 'No'}
        </span>
      ),
    },
    {
      key: 'date_joined',
      label: 'Joined',
      render: (row) => new Date(row.date_joined).toLocaleDateString(),
    },
  ];

  const filters = [
    {
      key: 'is_active',
      label: 'Status',
      options: [
        { value: 'true', label: 'Active' },
        { value: 'false', label: 'Inactive' },
      ],
    },
    {
      key: 'is_staff',
      label: 'Staff',
      options: [
        { value: 'true', label: 'Staff' },
        { value: 'false', label: 'Non-Staff' },
      ],
    },
  ];

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async (params = {}) => {
    setIsLoading(true);
    try {
      const response = await adminAPI.users.list(params);
      setUsers(response.data.results || response.data);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to fetch users');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (value) => {
    setSearchTerm(value);
    fetchUsers({ search: value });
  };

  const handleEdit = (user) => {
    // TODO: Open edit dialog/modal
    toast.info(`Edit user: ${user.username}`);
  };

  const handleDelete = async (user) => {
    if (window.confirm(`Are you sure you want to delete user "${user.username}"?`)) {
      try {
        await adminAPI.users.delete(user.id);
        toast.success('User deleted successfully');
        fetchUsers();
      } catch (error) {
        console.error('Error deleting user:', error);
        toast.error('Failed to delete user');
      }
    }
  };

  const handleAdd = () => {
    // TODO: Open add user dialog/modal
    toast.info('Add new user');
  };

  return (
    <div className="container mx-auto p-6">
      <AdminDataTable
        title="User Management"
        data={users}
        columns={columns}
        onAdd={handleAdd}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onSearch={handleSearch}
        filters={filters}
        isLoading={isLoading}
      />
    </div>
  );
}
