'use client';

import { useEffect, useState } from 'react';
import { Building2, Plus, Edit2, Trash2, Search, Download, X } from 'lucide-react';
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

interface Retailer {
  id: number;
  user: number;
  user_username: string;
  company_name: string;
  contact_person: string;
  phone_number: string;
  email: string;
  address: string;
  city: string;
  country: string;
  is_active: boolean;
  commission_percentage: string;
  payment_terms: string;
  branch_count: number;
  created_at: string;
  updated_at: string;
}

interface RetailerFormData {
  company_name: string;
  contact_person: string;
  phone_number: string;
  email: string;
  address: string;
  city: string;
  country: string;
  commission_percentage: string;
  payment_terms: string;
  is_active: boolean;
}

export default function RetailersPage() {
  const [retailers, setRetailers] = useState<Retailer[]>([]);
  const [filteredRetailers, setFilteredRetailers] = useState<Retailer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedRetailer, setSelectedRetailer] = useState<Retailer | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  // Form data
  const [formData, setFormData] = useState<RetailerFormData>({
    company_name: '',
    contact_person: '',
    phone_number: '',
    email: '',
    address: '',
    city: '',
    country: 'Zimbabwe',
    commission_percentage: '10.00',
    payment_terms: 'Net 30',
    is_active: true,
  });

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const fetchRetailers = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/crm-api/admin-panel/retailers/');
      setRetailers(response.data.results || response.data);
      setFilteredRetailers(response.data.results || response.data);
      setError(null);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRetailers();
  }, []);

  // Search filter
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredRetailers(retailers);
    } else {
      const filtered = retailers.filter((retailer) => {
        const search = searchTerm.toLowerCase();
        return (
          retailer.company_name.toLowerCase().includes(search) ||
          retailer.contact_person.toLowerCase().includes(search) ||
          retailer.email.toLowerCase().includes(search) ||
          retailer.phone_number.toLowerCase().includes(search) ||
          retailer.city.toLowerCase().includes(search)
        );
      });
      setFilteredRetailers(filtered);
    }
    setCurrentPage(1);
  }, [searchTerm, retailers]);

  // Pagination
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentItems = filteredRetailers.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredRetailers.length / itemsPerPage);

  const handleCreate = () => {
    setFormData({
      company_name: '',
      contact_person: '',
      phone_number: '',
      email: '',
      address: '',
      city: '',
      country: 'Zimbabwe',
      commission_percentage: '10.00',
      payment_terms: 'Net 30',
      is_active: true,
    });
    setCreateModalOpen(true);
  };

  const handleEdit = (retailer: Retailer) => {
    setSelectedRetailer(retailer);
    setFormData({
      company_name: retailer.company_name,
      contact_person: retailer.contact_person,
      phone_number: retailer.phone_number,
      email: retailer.email,
      address: retailer.address,
      city: retailer.city,
      country: retailer.country,
      commission_percentage: retailer.commission_percentage,
      payment_terms: retailer.payment_terms,
      is_active: retailer.is_active,
    });
    setEditModalOpen(true);
  };

  const handleDelete = (retailer: Retailer) => {
    setSelectedRetailer(retailer);
    setDeleteModalOpen(true);
  };

  const handleSubmitCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await apiClient.post('/crm-api/admin-panel/retailers/', formData);
      await fetchRetailers();
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
    if (!selectedRetailer) return;
    
    setIsSubmitting(true);
    try {
      await apiClient.patch(`/crm-api/admin-panel/retailers/${selectedRetailer.id}/`, formData);
      await fetchRetailers();
      setEditModalOpen(false);
      setError(null);
    } catch (err: any) {
      setError(extractErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!selectedRetailer) return;
    
    setIsSubmitting(true);
    try {
      await apiClient.delete(`/crm-api/admin-panel/retailers/${selectedRetailer.id}/`);
      await fetchRetailers();
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
    doc.text('Retailers Report', 14, 22);
    doc.setFontSize(11);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 30);
    
    autoTable(doc, {
      startY: 35,
      head: [['Company', 'Contact Person', 'Email', 'Phone', 'City', 'Branches', 'Status']],
      body: filteredRetailers.map(r => [
        r.company_name,
        r.contact_person,
        r.email,
        r.phone_number,
        r.city,
        r.branch_count.toString(),
        r.is_active ? 'Active' : 'Inactive'
      ]),
    });
    
    doc.save(`retailers_${new Date().toISOString().split('T')[0]}.pdf`);
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
          <Building2 className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Retailers</h1>
            <p className="text-sm text-gray-500">Manage retailer accounts and partnerships</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleExportPDF} variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
          <Button onClick={handleCreate} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            Add Retailer
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
            placeholder="Search retailers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Retailers ({filteredRetailers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-3 font-semibold">Company</th>
                  <th className="text-left p-3 font-semibold">Contact Person</th>
                  <th className="text-left p-3 font-semibold">Email</th>
                  <th className="text-left p-3 font-semibold">Phone</th>
                  <th className="text-left p-3 font-semibold">City</th>
                  <th className="text-left p-3 font-semibold">Branches</th>
                  <th className="text-left p-3 font-semibold">Status</th>
                  <th className="text-left p-3 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {currentItems.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center p-8 text-gray-500">
                      No retailers found
                    </td>
                  </tr>
                ) : (
                  currentItems.map((retailer) => (
                    <tr key={retailer.id} className="border-b hover:bg-gray-50">
                      <td className="p-3 font-medium">{retailer.company_name}</td>
                      <td className="p-3">{retailer.contact_person}</td>
                      <td className="p-3 text-sm">{retailer.email}</td>
                      <td className="p-3">{retailer.phone_number}</td>
                      <td className="p-3">{retailer.city}</td>
                      <td className="p-3 text-center">{retailer.branch_count}</td>
                      <td className="p-3">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          retailer.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {retailer.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleEdit(retailer)}
                          >
                            <Edit2 className="w-4 h-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(retailer)}
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
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add New Retailer</DialogTitle>
            <DialogDescription>
              Create a new retailer account for partnership management
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitCreate} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="company_name">Company Name *</Label>
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="contact_person">Contact Person *</Label>
                <Input
                  id="contact_person"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="phone_number">Phone Number *</Label>
                <Input
                  id="phone_number"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                  required
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="address">Address</Label>
                <Input
                  id="address"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="city">City</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => setFormData({...formData, city: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="country">Country</Label>
                <Input
                  id="country"
                  value={formData.country}
                  onChange={(e) => setFormData({...formData, country: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="commission_percentage">Commission %</Label>
                <Input
                  id="commission_percentage"
                  type="number"
                  step="0.01"
                  value={formData.commission_percentage}
                  onChange={(e) => setFormData({...formData, commission_percentage: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="payment_terms">Payment Terms</Label>
                <Input
                  id="payment_terms"
                  value={formData.payment_terms}
                  onChange={(e) => setFormData({...formData, payment_terms: e.target.value})}
                />
              </div>
              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm">Active</span>
                </label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Creating...' : 'Create Retailer'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Retailer</DialogTitle>
            <DialogDescription>
              Update retailer information
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmitEdit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="edit_company_name">Company Name *</Label>
                <Input
                  id="edit_company_name"
                  value={formData.company_name}
                  onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit_contact_person">Contact Person *</Label>
                <Input
                  id="edit_contact_person"
                  value={formData.contact_person}
                  onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit_email">Email *</Label>
                <Input
                  id="edit_email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  required
                />
              </div>
              <div>
                <Label htmlFor="edit_phone_number">Phone Number *</Label>
                <Input
                  id="edit_phone_number"
                  value={formData.phone_number}
                  onChange={(e) => setFormData({...formData, phone_number: e.target.value})}
                  required
                />
              </div>
              <div className="col-span-2">
                <Label htmlFor="edit_address">Address</Label>
                <Input
                  id="edit_address"
                  value={formData.address}
                  onChange={(e) => setFormData({...formData, address: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_city">City</Label>
                <Input
                  id="edit_city"
                  value={formData.city}
                  onChange={(e) => setFormData({...formData, city: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_country">Country</Label>
                <Input
                  id="edit_country"
                  value={formData.country}
                  onChange={(e) => setFormData({...formData, country: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_commission_percentage">Commission %</Label>
                <Input
                  id="edit_commission_percentage"
                  type="number"
                  step="0.01"
                  value={formData.commission_percentage}
                  onChange={(e) => setFormData({...formData, commission_percentage: e.target.value})}
                />
              </div>
              <div>
                <Label htmlFor="edit_payment_terms">Payment Terms</Label>
                <Input
                  id="edit_payment_terms"
                  value={formData.payment_terms}
                  onChange={(e) => setFormData({...formData, payment_terms: e.target.value})}
                />
              </div>
              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.is_active}
                    onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm">Active</span>
                </label>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Updating...' : 'Update Retailer'}
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
              Are you sure you want to delete retailer "{selectedRetailer?.company_name}"?
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
