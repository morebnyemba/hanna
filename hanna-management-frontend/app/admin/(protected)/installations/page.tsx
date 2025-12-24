'use client';

import { useEffect, useState } from 'react';
import { FiTool, FiUser, FiMapPin, FiCalendar, FiSearch, FiPackage, FiCheckCircle, FiClock, FiPlus, FiEdit, FiTrash2, FiDownload, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { DateRange } from 'react-day-picker';
import { subDays, format } from 'date-fns';
import { DateRangePicker } from '@/app/components/DateRangePicker';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';

interface Technician {
  id: number;
  user: {
    id: number;
    username: string;
    full_name: string;
  };
}

interface Installation {
  id: number;
  full_name: string;
  address: string;
  contact_phone: string;
  installation_type: string;
  installation_type_display: string;
  status: string;
  status_display: string;
  order_number: string | null;
  technicians: Technician[];
  created_at: string;
  updated_at: string;
  notes: string | null;
  associated_order: {
    id: string;
    order_number: string;
    items: {
      id: string;
      product_name: string;
      product_sku: string;
      quantity: number;
    }[];
  } | null;
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  scheduled: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-purple-100 text-purple-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

export default function AdminInstallationsPage() {
  const [installations, setInstallations] = useState<Installation[]>([]);
  const [selectedInstallation, setSelectedInstallation] = useState<Installation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [date, setDate] = useState<DateRange | undefined>({
    from: subDays(new Date(), 90),
    to: new Date(),
  });
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [installationToDelete, setInstallationToDelete] = useState<Installation | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [filteredInstallations, setFilteredInstallations] = useState<Installation[]>([]);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [availableTechnicians, setAvailableTechnicians] = useState<Technician[]>([]);
  const [selectedTechIds, setSelectedTechIds] = useState<number[]>([]);
  const [assignLoading, setAssignLoading] = useState(false);

  const fetchInstallations = async () => {
    setLoading(true);
    setError(null);
    try {
      let url = '/crm-api/admin-panel/installation-requests/';
      const params = new URLSearchParams();
      
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await apiClient.get(url);
      setInstallations(response.data.results || response.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch installations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInstallations();
  }, [statusFilter]);

  const handleMarkCompleted = async (installation: Installation) => {
    try {
      await apiClient.post(`/crm-api/admin-panel/installation-requests/${installation.id}/mark_completed/`);
      // Refresh the list
      fetchInstallations();
      // Update selected installation if it's the same
      if (selectedInstallation?.id === installation.id) {
        setSelectedInstallation({ ...installation, status: 'completed', status_display: 'Completed' });
      }
    } catch (err: any) {
      alert('Failed to mark installation as completed: ' + (err.response?.data?.message || err.message));
    }
  };

  const handleDeleteClick = (installation: Installation) => {
    setInstallationToDelete(installation);
    setDeleteModalOpen(true);
  };

  const openAssignModal = async (installation: Installation) => {
    setSelectedInstallation(installation);
    setAssignModalOpen(true);
    setAssignLoading(true);
    try {
      const res = await apiClient.get('/crm-api/admin-panel/technicians/');
      setAvailableTechnicians(res.data.results || res.data);
      const current = (installation.technicians || []).map((t) => t.id);
      setSelectedTechIds(current);
    } catch (e: any) {
      console.error('Failed to load technicians', e);
      alert('Failed to load technicians: ' + (e.response?.data?.detail || e.message));
    } finally {
      setAssignLoading(false);
    }
  };

  const toggleTech = (id: number) => {
    setSelectedTechIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedInstallation) return;
    setAssignLoading(true);
    try {
      const res = await apiClient.post(
        `/crm-api/admin-panel/installation-requests/${selectedInstallation.id}/assign_technicians/`,
        { technician_ids: selectedTechIds }
      );
      // Update list and selected installation
      setInstallations((prev) =>
        prev.map((inst) =>
          inst.id === selectedInstallation.id
            ? { ...inst, technicians: availableTechnicians.filter((t) => selectedTechIds.includes(t.id)) as any }
            : inst
        )
      );
      setSelectedInstallation((prev) =>
        prev ? { ...prev, technicians: availableTechnicians.filter((t) => selectedTechIds.includes(t.id)) as any } : prev
      );
      setAssignModalOpen(false);
    } catch (e: any) {
      alert('Failed to assign technicians: ' + (e.response?.data?.detail || e.message));
    } finally {
      setAssignLoading(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!installationToDelete) return;
    
    setIsDeleting(true);
    try {
      await apiClient.delete(`/crm-api/admin-panel/installation-requests/${installationToDelete.id}/`);
      // Remove from list
      setInstallations(prev => prev.filter(i => i.id !== installationToDelete.id));
      // Clear selection if deleted
      if (selectedInstallation?.id === installationToDelete.id) {
        setSelectedInstallation(null);
      }
      setDeleteModalOpen(false);
      setInstallationToDelete(null);
    } catch (err: any) {
      alert('Failed to delete installation: ' + (err.response?.data?.message || err.message));
    } finally {
      setIsDeleting(false);
    }
  };

  // Client-side filtering + pagination
  useEffect(() => {
    let filtered = installations.filter((installation) => {
      const matchesSearch =
        installation.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        installation.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (installation.order_number || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        installation.technicians?.some(
          (t) =>
            (t.user?.full_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
            (t.user?.username || '').toLowerCase().includes(searchTerm.toLowerCase())
        );

      const matchesStatus = statusFilter === 'all' || installation.status === statusFilter;

      const created = new Date(installation.created_at);
      const inRange = !date?.from || !date?.to || (created >= (date.from as Date) && created <= (date.to as Date));

      return matchesSearch && matchesStatus && inRange;
    });

    setFilteredInstallations(filtered);
    setCurrentPage(1);
  }, [installations, searchTerm, statusFilter, date]);

  const totalPages = Math.ceil(filteredInstallations.length / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = filteredInstallations.slice(startIndex, endIndex);

  const handleExportPDF = () => {
    const doc = new jsPDF();
    doc.setFontSize(18);
    doc.text('Installations Report', 14, 22);
    doc.setFontSize(11);
    const dateRangeStr = date?.from && date?.to ? `${format(date.from, 'MMM dd, yyyy')} - ${format(date.to, 'MMM dd, yyyy')}` : 'All time';
    doc.text(`Generated: ${new Date().toLocaleDateString()} | Range: ${dateRangeStr}`, 14, 30);

    const rows = filteredInstallations.map((i) => [
      i.full_name,
      i.address,
      i.installation_type_display || i.installation_type,
      i.status_display || i.status,
      i.order_number || '-',
      format(new Date(i.created_at), 'MMM dd, yyyy'),
    ]);

    autoTable(doc, {
      head: [['Customer', 'Address', 'Type', 'Status', 'Order #', 'Date']],
      body: rows,
      startY: 35,
      theme: 'grid',
      headStyles: { fillColor: [124, 58, 237] },
    });

    doc.save(`installations-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FiTool className="w-6 h-6" /> Installation Tracking
        </h1>
        <div className="flex gap-2 w-full sm:w-auto flex-wrap items-center">
          <div className="relative flex-1 sm:w-64">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search installations or technicians..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          <div className="flex items-center gap-2">
            <DateRangePicker date={date} setDate={setDate} />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="border rounded px-3 py-2 text-sm"
            >
              <option value="all">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="scheduled">Scheduled</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
            </select>

            <Button onClick={handleExportPDF} className="bg-purple-600 hover:bg-purple-700 text-white flex items-center gap-2">
              <FiDownload className="w-4 h-4" /> Export PDF
            </Button>
          </div>
        </div>
      </div>
      
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      {/* Stats Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-yellow-500">
          <p className="text-sm text-gray-500">Pending</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'pending').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-blue-500">
          <p className="text-sm text-gray-500">Scheduled</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'scheduled').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
          <p className="text-sm text-gray-500">In Progress</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'in_progress').length}</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
          <p className="text-sm text-gray-500">Completed</p>
          <p className="text-2xl font-bold">{installations.filter(i => i.status === 'completed').length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Installations List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiTool className="w-5 h-5" /> All Installations
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse bg-gray-100 h-24 rounded-lg"></div>
                  ))}
                </div>
              ) : filteredInstallations.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No installations found.</p>
              ) : (
                <>
                  <div className="space-y-4">
                  {currentItems.map((installation) => (
                    <div
                      key={installation.id}
                      className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                        selectedInstallation?.id === installation.id ? 'border-purple-500 bg-purple-50' : ''
                      }`}
                      onClick={() => setSelectedInstallation(installation)}
                    >
                      <div className="flex justify-between items-start">
                        <div className="space-y-1 flex-1">
                          <div className="flex items-center gap-2">
                            <FiUser className="w-4 h-4 text-gray-500" />
                            <span className="font-medium">{installation.full_name}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm text-gray-600">
                            <FiMapPin className="w-4 h-4" />
                            <span className="truncate max-w-xs">{installation.address}</span>
                          </div>
                          <div className="text-xs text-gray-500">
                            {installation.order_number && (
                              <span className="mr-2">Order: {installation.order_number}</span>
                            )}
                            <span>{format(new Date(installation.created_at), 'MMM dd, yyyy')}</span>
                          </div>
                          {/* Technicians */}
                          {installation.technicians && installation.technicians.length > 0 && (
                            <div className="flex items-center gap-2 text-xs text-gray-600">
                              <FiTool className="w-3 h-3" />
                              <span>
                                {installation.technicians.map(t => t.user?.full_name || t.user?.username).join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                        <div className="flex flex-col items-end gap-2">
                          <Badge className={statusColors[installation.status] || 'bg-gray-100'}>
                            {installation.status === 'completed' ? (
                              <FiCheckCircle className="w-3 h-3 mr-1" />
                            ) : (
                              <FiClock className="w-3 h-3 mr-1" />
                            )}
                            {installation.status_display || installation.status}
                          </Badge>
                          <span className="text-xs text-gray-500">
                            {installation.installation_type_display || installation.installation_type}
                          </span>
                          {/* Action Buttons */}
                          <div className="flex gap-1 mt-2" onClick={(e) => e.stopPropagation()}>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openAssignModal(installation)}
                              className="text-xs px-2 py-1 h-7"
                              title="Assign Technicians"
                            >
                              <FiTool className="w-3 h-3 mr-1" /> Assign
                            </Button>
                            {installation.status !== 'completed' && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleMarkCompleted(installation)}
                                className="text-xs px-2 py-1 h-7"
                                title="Mark as Completed"
                              >
                                <FiCheckCircle className="w-3 h-3 mr-1" />
                                Complete
                              </Button>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDeleteClick(installation)}
                              className="text-xs px-2 py-1 h-7 text-red-600 hover:text-red-700"
                              title="Delete Installation"
                            >
                              <FiTrash2 className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                  </div>
                  {totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-6 pt-4 border-t">
                    <button
                      onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="flex items-center gap-2 px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 rounded"
                    >
                      <FiChevronLeft /> Previous
                    </button>
                    <span className="text-sm text-gray-600">Page {currentPage} of {totalPages}</span>
                    <button
                      onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="flex items-center gap-2 px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 rounded"
                    >
                      Next <FiChevronRight />
                    </button>
                  </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Installation Detail */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiPackage className="w-5 h-5" /> Installation Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedInstallation ? (
                <p className="text-gray-500 text-center py-8">Select an installation to view details</p>
              ) : (
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Customer</p>
                    <p className="font-medium">{selectedInstallation.full_name}</p>
                    <p className="text-sm text-gray-600">{selectedInstallation.contact_phone}</p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Address</p>
                    <p className="text-sm">{selectedInstallation.address}</p>
                  </div>

                  <div className="flex items-center gap-2">
                    <Badge className={statusColors[selectedInstallation.status] || 'bg-gray-100'}>
                      {selectedInstallation.status_display || selectedInstallation.status}
                    </Badge>
                    <Badge variant="outline">
                      {selectedInstallation.installation_type_display || selectedInstallation.installation_type}
                    </Badge>
                  </div>

                  {/* Assigned Technicians */}
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Assigned Technicians</p>
                    {selectedInstallation.technicians && selectedInstallation.technicians.length > 0 ? (
                      <div className="space-y-1">
                        {selectedInstallation.technicians.map((tech) => (
                          <div key={tech.id} className="flex items-center gap-2 text-sm">
                            <FiUser className="w-4 h-4 text-gray-400" />
                            <span>{tech.user?.full_name || tech.user?.username}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-gray-400">No technicians assigned</p>
                    )}
                  </div>

                  {selectedInstallation.notes && (
                    <div>
                      <p className="text-sm text-gray-500">Notes</p>
                      <p className="text-sm">{selectedInstallation.notes}</p>
                    </div>
                  )}

                  {selectedInstallation.associated_order && (
                    <div className="pt-4 border-t">
                      <p className="text-sm font-medium mb-2">Order Items</p>
                      <div className="space-y-2">
                        {selectedInstallation.associated_order.items.map((item) => (
                          <div key={item.id} className="bg-gray-50 p-2 rounded text-sm">
                            <div className="flex justify-between">
                              <span className="font-medium">{item.product_name}</span>
                              <span className="text-gray-500">x{item.quantity}</span>
                            </div>
                            <p className="text-xs text-gray-500">SKU: {item.product_sku}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="text-xs text-gray-400 pt-2 border-t">
                    <p>Created: {format(new Date(selectedInstallation.created_at), 'MMM dd, yyyy HH:mm')}</p>
                    <p>Updated: {format(new Date(selectedInstallation.updated_at), 'MMM dd, yyyy HH:mm')}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={() => {
          setDeleteModalOpen(false);
          setInstallationToDelete(null);
        }}
        onConfirm={handleDeleteConfirm}
        title="Delete Installation Request"
        message={`Are you sure you want to delete the installation request for "${installationToDelete?.full_name}"? This action cannot be undone.`}
        isDeleting={isDeleting}
      />

      {/* Assign Technicians Modal */}
      <Dialog open={assignModalOpen} onOpenChange={setAssignModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Technicians</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAssignSubmit} className="space-y-4">
            <div className="max-h-64 overflow-auto border rounded p-2">
              {assignLoading ? (
                <p className="text-sm text-gray-500">Loading technicians...</p>
              ) : availableTechnicians.length === 0 ? (
                <p className="text-sm text-gray-500">No technicians available.</p>
              ) : (
                availableTechnicians.map((tech) => (
                  <label key={tech.id} className="flex items-center gap-2 py-1">
                    <input
                      type="checkbox"
                      checked={selectedTechIds.includes(tech.id)}
                      onChange={() => toggleTech(tech.id)}
                    />
                    <span className="text-sm">{tech.user?.full_name || tech.user?.username || `Technician #${tech.id}`}</span>
                  </label>
                ))
              )}
            </div>
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={() => setAssignModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={assignLoading} className="bg-purple-600 hover:bg-purple-700">
                {assignLoading ? 'Assigning...' : 'Assign'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </main>
  );
}
