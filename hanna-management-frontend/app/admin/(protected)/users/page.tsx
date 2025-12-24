'use client';

import { useState, useEffect } from 'react';
import { FiUsers, FiPlus, FiDownload, FiSearch, FiEdit, FiTrash2, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';

interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  groups: string[];
  is_active: boolean;
  date_joined: string;
}

const SkeletonRow = () => (
  <tr className="animate-pulse">
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-full"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </td>
    <td className="px-4 py-3 sm:px-6 sm:py-4">
      <div className="h-4 bg-gray-200 rounded w-24"></div>
    </td>
  </tr>
);

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isInviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [isEditDialogOpen, setEditDialogOpen] = useState(false);
  const itemsPerPage = 10;

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get('/crm-api/users/');
        setUsers(response.data.results);
        setFilteredUsers(response.data.results);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch users.');
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  // Search filter
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredUsers(users);
    } else {
      const filtered = users.filter(user => {
        const fullName = `${user.first_name} ${user.last_name}`.toLowerCase();
        const email = user.email?.toLowerCase() || '';
        const username = user.username?.toLowerCase() || '';
        const search = searchTerm.toLowerCase();
        return fullName.includes(search) || email.includes(search) || username.includes(search);
      });
      setFilteredUsers(filtered);
      setCurrentPage(1);
    }
  }, [searchTerm, users]);

  // Pagination
  const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentUsers = filteredUsers.slice(startIndex, endIndex);

  // PDF Export
  const handleExportPDF = () => {
    const doc = new jsPDF();
    
    doc.setFontSize(18);
    doc.text('Users Report', 14, 22);
    
    doc.setFontSize(11);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 30);
    
    const tableData = filteredUsers.map(user => [
      `${user.first_name} ${user.last_name}`,
      user.email,
      user.username,
      Array.isArray(user.groups) ? user.groups.join(', ') : '',
    ]);
    
    autoTable(doc, {
      head: [['Name', 'Email', 'Username', 'Roles']],
      body: tableData,
      startY: 35,
      theme: 'grid',
      headStyles: { fillColor: [124, 58, 237] },
    });
    
    doc.save(`users-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const handleDeleteClick = (user: User) => {
    setUserToDelete(user);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!userToDelete) return;

    setIsDeleting(true);
    try {
      await apiClient.delete(`/crm-api/users/${userToDelete.id}/`);
      setUsers(users.filter(u => u.id !== userToDelete.id));
      setDeleteModalOpen(false);
      setUserToDelete(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setUserToDelete(null);
  };

  const handleEditClick = (user: User) => {
    setEditingUser(user);
    setEditDialogOpen(true);
  };

  const handleEditUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!editingUser) return;

    const formData = new FormData(event.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await apiClient.put(`/crm-api/users/${editingUser.id}/`, data);
      setUsers(users.map(u => u.id === editingUser.id ? response.data : u));
      setEditDialogOpen(false);
      setEditingUser(null);
    } catch (err: any) {
      alert('Failed to update user: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleInviteUser = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      await apiClient.post('/crm-api/users/invite/', data);
      setInviteDialogOpen(false);
      // Refresh users list
      const response = await apiClient.get('/crm-api/users/');
      setUsers(response.data.results);
      setFilteredUsers(response.data.results);
    } catch (err: any) {
      alert('Failed to invite user: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <>
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiUsers className="mr-3" />
          User Management
        </h1>
        <div className="flex gap-2">
          <button
            onClick={handleExportPDF}
            className="flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition"
            disabled={filteredUsers.length === 0}
          >
            <FiDownload className="mr-2" />
            Export PDF
          </button>
          <Dialog open={isInviteDialogOpen} onOpenChange={setInviteDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <FiPlus className="mr-2" />
                Invite User
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Invite New User</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleInviteUser} className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input id="email" name="email" type="email" required />
                </div>
                <div>
                  <Label htmlFor="first_name">First Name</Label>
                  <Input id="first_name" name="first_name" required />
                </div>
                <div>
                  <Label htmlFor="last_name">Last Name</Label>
                  <Input id="last_name" name="last_name" required />
                </div>
                <div>
                  <Label htmlFor="role">Role</Label>
                  <select id="role" name="role" className="w-full p-2 border rounded">
                    <option>Admin</option>
                    <option>Manufacturer</option>
                    <option>Technician</option>
                  </select>
                </div>
                <Button type="submit">Send Invitation</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-4 relative">
        <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name, email, or username..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      {error && <p className="text-red-500 mb-4">Error: {error}</p>}

      <div className="bg-white p-3 sm:p-6 rounded-lg shadow-md border border-gray-200">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th scope="col" className="px-4 py-3 sm:px-6 sm:py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <>
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                  <SkeletonRow />
                </>
              ) : currentUsers.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-8 sm:px-6 text-center text-gray-500">
                    {searchTerm ? 'No users found matching your search' : 'No users found'}
                  </td>
                </tr>
              ) : (
                currentUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 transition-colors duration-150">
                    <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm font-medium text-gray-900">
                      {user.first_name} {user.last_name}
                    </td>
                    <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                      {user.email}
                    </td>
                    <td className="px-4 py-3 sm:px-6 sm:py-4 text-sm text-gray-500">
                      {Array.isArray(user.groups) ? user.groups.join(', ') : ''}
                    </td>
                    <td className="px-4 py-3 sm:px-6 sm:py-4">
                      <div className="flex items-center gap-1 sm:gap-2">
                        <button
                          onClick={() => handleEditClick(user)}
                          className="p-1.5 sm:p-2 text-blue-600 hover:bg-blue-50 rounded-md transition"
                          title="Edit"
                        >
                          <FiEdit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteClick(user)}
                          className="p-1.5 sm:p-2 text-red-600 hover:bg-red-50 rounded-md transition"
                          title="Delete"
                        >
                          <FiTrash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {!loading && totalPages > 1 && (
          <div className="mt-4 flex flex-col sm:flex-row items-center justify-between border-t border-gray-200 pt-4 gap-3">
            <div className="text-xs sm:text-sm text-gray-700">
              Showing {startIndex + 1} to {Math.min(endIndex, filteredUsers.length)} of {filteredUsers.length} users
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FiChevronLeft />
              </button>
              <span className="px-3 py-1 text-xs sm:text-sm">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="p-2 border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FiChevronRight />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditUser} className="space-y-4">
            <div>
              <Label htmlFor="edit_email">Email</Label>
              <Input 
                id="edit_email" 
                name="email" 
                type="email" 
                defaultValue={editingUser?.email}
                required 
              />
            </div>
            <div>
              <Label htmlFor="edit_first_name">First Name</Label>
              <Input 
                id="edit_first_name" 
                name="first_name" 
                defaultValue={editingUser?.first_name}
                required 
              />
            </div>
            <div>
              <Label htmlFor="edit_last_name">Last Name</Label>
              <Input 
                id="edit_last_name" 
                name="last_name" 
                defaultValue={editingUser?.last_name}
                required 
              />
            </div>
            <div>
              <Label htmlFor="edit_role">Role</Label>
              <select 
                id="edit_role" 
                name="role" 
                className="w-full p-2 border rounded"
                defaultValue={editingUser?.groups?.[0] || ''}
              >
                <option>Admin</option>
                <option>Manufacturer</option>
                <option>Technician</option>
              </select>
            </div>
            <Button type="submit">Update User</Button>
          </form>
        </DialogContent>
      </Dialog>

      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete User"
        message={`Are you sure you want to delete "${userToDelete?.first_name} ${userToDelete?.last_name}"? This action cannot be undone.`}
        isDeleting={isDeleting}
      />
    </>
  );
}
