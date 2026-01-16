'use client';

import { useEffect, useState } from 'react';
import { Factory, Plus, Edit2, Trash2, Search, Download, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

interface Manufacturer {
  id: number;
  name: string;
  contact_email: string;
  user: number | null;
  user_username: string | null;
  created_at?: string;
}

interface ManufacturerFormData {
  name: string;
  contact_email: string;
}

export default function ManufacturersPage() {
  const [manufacturers, setManufacturers] = useState<Manufacturer[]>([]);
  const [filteredManufacturers, setFilteredManufacturers] = useState<Manufacturer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedManufacturer, setSelectedManufacturer] = useState<Manufacturer | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState<ManufacturerFormData>({
    name: '',
    contact_email: '',
  });

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const fetchManufacturers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/crm-api/admin-panel/manufacturers/');
      setManufacturers(response.data.results || response.data);
      setFilteredManufacturers(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchManufacturers();
  }, []);

  // Search filter
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredManufacturers(manufacturers);
    } else {
      const filtered = manufacturers.filter((manufacturer) => {
        const search = searchTerm.toLowerCase();
        return (
          manufacturer.name.toLowerCase().includes(search) ||
          manufacturer.contact_email?.toLowerCase().includes(search) ||
          manufacturer.user_username?.toLowerCase().includes(search)
        );
      });
      setFilteredManufacturers(filtered);
    }
    setCurrentPage(1);
  }, [searchTerm, manufacturers]);

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredManufacturers.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredManufacturers.length / itemsPerPage);

  const handleCreate = () => {
    setFormData({
      name: '',
      contact_email: '',
    });
    setCreateModalOpen(true);
  };

  const handleEdit = (manufacturer: Manufacturer) => {
    setSelectedManufacturer(manufacturer);
    setFormData({
      name: manufacturer.name,
      contact_email: manufacturer.contact_email || '',
    });
    setEditModalOpen(true);
  };

  const handleDelete = (manufacturer: Manufacturer) => {
    setSelectedManufacturer(manufacturer);
    setDeleteModalOpen(true);
  };

  const handleSubmitCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.post('/crm-api/admin-panel/manufacturers/', formData);
      await fetchManufacturers();
      setCreateModalOpen(false);
      setError(null);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmitEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedManufacturer) return;
    
    setIsSubmitting(true);
    try {
      await apiClient.patch(`/crm-api/admin-panel/manufacturers/${selectedManufacturer.id}/`, formData);
      await fetchManufacturers();
      setEditModalOpen(false);
      setError(null);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedManufacturer) return;
    
    setIsSubmitting(true);
    try {
      await apiClient.delete(`/crm-api/admin-panel/manufacturers/${selectedManufacturer.id}/`);
      await fetchManufacturers();
      setDeleteModalOpen(false);
      setError(null);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExportPDF = () => {
    const doc = new jsPDF();
    doc.setFontSize(18);
    doc.text('Manufacturers Report', 14, 22);
    doc.setFontSize(11);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
    
    autoTable(doc, {
      startY: 35,
      head: [['Manufacturer Name', 'Contact Email', 'User Account']],
      body: filteredManufacturers.map(m => [
        m.name,
        m.contact_email || 'N/A',
        m.user_username || 'None'
      ]),
    });
    
    doc.save(`manufacturers_${new Date().toISOString().split('T')[0]}.pdf`);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex items-center gap-3">
          <Factory className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Manufacturers</h1>
            <p className="text-sm text-gray-500">Manage product manufacturers and suppliers</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleExportPDF} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
          <Button onClick={handleCreate} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Manufacturer
          </Button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded relative">
          <span className="block sm:inline">{error}</span>
          <button
            className="absolute top-0 bottom-0 right-0 px-4 py-3"
            onClick={() => setError(null)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Search */}
      <div className="flex items-center gap-2 max-w-md">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <Input
            placeholder="Search manufacturers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Manufacturers ({filteredManufacturers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-semibold">Manufacturer Name</th>
                  <th className="text-left p-3 font-semibold">Contact Email</th>
                  <th className="text-left p-3 font-semibold">User Account</th>
                  <th className="text-left p-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentItems.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="text-center p-8 text-gray-500">
                      No manufacturers found
                    </td>
                  </tr>
                ) : (
                  currentItems.map((manufacturer) => (
                    <tr key={manufacturer.id} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{manufacturer.name}</td>
                      <td className="p-3 text-sm">{manufacturer.contact_email || 'N/A'}</td>
                      <td className="p-3">
                        {manufacturer.user_username ? (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {manufacturer.user_username}
                          </span>
                        ) : (
                          <span className="text-gray-400 text-sm">No account</span>
                        )}
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(manufacturer)}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(manufacturer)}
                            className="text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-2 mt-4">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                Previous
              </Button>
              <span className="text-sm">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Modal */}
      <Dialog open={createModalOpen} onOpenChange={setCreateModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Add New Manufacturer</DialogTitle>
            <DialogDescription>
              Create a new manufacturer entry for product tracking
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitCreate} className="space-y-4">
            <div>
              <Label htmlFor="name">Manufacturer Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
                placeholder="Enter manufacturer name"
              />
            </div>
            <div>
              <Label htmlFor="contact_email">Contact Email</Label>
              <Input
                id="contact_email"
                type="email"
                value={formData.contact_email}
                onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
                placeholder="contact@manufacturer.com"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creating...' : 'Create Manufacturer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Manufacturer</DialogTitle>
            <DialogDescription>
              Update manufacturer information
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitEdit} className="space-y-4">
            <div>
              <Label htmlFor="edit_name">Manufacturer Name *</Label>
              <Input
                id="edit_name"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                required
              />
            </div>
            <div>
              <Label htmlFor="edit_contact_email">Contact Email</Label>
              <Input
                id="edit_contact_email"
                type="email"
                value={formData.contact_email}
                onChange={(e) => setFormData({...formData, contact_email: e.target.value})}
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Updating...' : 'Update Manufacturer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Modal */}
      <Dialog open={deleteModalOpen} onOpenChange={setDeleteModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Deletion</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete manufacturer "{selectedManufacturer?.name}"?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleConfirmDelete}
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
