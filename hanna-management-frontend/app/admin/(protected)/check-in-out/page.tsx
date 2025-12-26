'use client';

import { useEffect, useState, Component, ReactNode } from 'react';
import apiClient from '@/app/lib/apiClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { AlertCircle, CheckCircle, Download, Package, Trash2, Filter, X, TrendingUp } from 'lucide-react';
import { subDays, format } from 'date-fns';
import CheckInOutManager from '@/app/components/CheckInOutManager';
import { extractErrorMessage } from '@/app/lib/apiUtils';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Interfaces
interface PaginatedResponse<T> {
  results: T[];
  next: string | null;
  previous?: string | null;
  count?: number;
}

interface ItemLocationHistory {
  id: string;
  serialized_item: {
    id: string;
    serial_number: string;
    barcode: string;
    product: { id: string; name: string };
    status: string;
    current_location: string;
  };
  from_location: string | null;
  to_location: string;
  transfer_reason: string;
  from_holder?: { id: string; username: string; full_name: string } | null;
  to_holder?: { id: string; username: string; full_name: string } | null;
  timestamp: string;
  notes?: string;
}

// Error Boundary
interface LocalErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class LocalErrorBoundary extends Component<{ children: ReactNode }, LocalErrorBoundaryState> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): LocalErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-800">Rendering Error</h3>
              <p className="text-sm text-red-700 mt-1">{this.state.error?.message}</p>
              {process.env.NODE_ENV === 'development' && (
                <pre className="text-xs text-red-600 mt-2 overflow-auto max-h-32">
                  {this.state.error?.stack}
                </pre>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Helpers
function safeFormatDate(value: string | Date | undefined | null, withTime = false): string {
  try {
    if (!value) return 'N/A';
    const date = typeof value === 'string' ? new Date(value) : value;
    if (isNaN(date.getTime())) return 'Invalid Date';
    return withTime
      ? format(date, 'MMM dd, yyyy · HH:mm')
      : format(date, 'MMM dd, yyyy');
  } catch {
    return 'Invalid Date';
  }
}

function toRelative(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.pathname + parsed.search;
  } catch {
    return url;
  }
}

// Main Component
export default function AdminCheckInOutPage() {
  const [view, setView] = useState<'list' | 'scanner'>('list');
  const [items, setItems] = useState<ItemLocationHistory[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFrom, setDateFrom] = useState(subDays(new Date(), 30).toISOString().split('T')[0]);
  const [dateTo, setDateTo] = useState(new Date().toISOString().split('T')[0]);
  const [selectedHistory, setSelectedHistory] = useState<ItemLocationHistory | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const filteredItems = items.filter(item => {
    const matchesSearch =
      item.serialized_item?.serial_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.serialized_item?.barcode?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.serialized_item?.product?.name?.toLowerCase().includes(searchTerm.toLowerCase());

    const itemDate = new Date(item.timestamp);
    const fromDate = new Date(dateFrom);
    const toDate = new Date(dateTo);
    toDate.setHours(23, 59, 59, 999);
    const matchesDate = itemDate >= fromDate && itemDate <= toDate;

    return matchesSearch && matchesDate;
  });

  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const paginatedItems = filteredItems.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      let url: string | null = '/crm-api/products/item-location-history/?ordering=-timestamp';
      const all: ItemLocationHistory[] = [];

      while (url) {
        const resp = await apiClient.get<PaginatedResponse<ItemLocationHistory> | ItemLocationHistory[]>(url);
        const pageItems = Array.isArray(resp.data) ? resp.data : resp.data.results || [];
        all.push(...pageItems);
        url = toRelative(Array.isArray(resp.data) ? null : (resp.data as PaginatedResponse<ItemLocationHistory>).next);
      }

      setItems(all);
      setCurrentPage(1);
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to load check-in/check-out records'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await apiClient.delete(`/crm-api/products/item-location-history/${deleteConfirm}/`);
      setItems(items.filter(i => i.id !== deleteConfirm));
      setDeleteConfirm(null);
      setSelectedHistory(null);
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to delete record'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    const tableData = filteredItems.map(item => [
      item.serialized_item?.serial_number || 'N/A',
      item.serialized_item?.product?.name || 'N/A',
      item.from_location ? item.from_location.replace('_', ' ').toUpperCase() : 'N/A',
      item.to_location.replace('_', ' ').toUpperCase(),
      item.transfer_reason.replace('_', ' ').toUpperCase(),
      safeFormatDate(item.timestamp),
    ]);

    autoTable(doc, {
      head: [['Serial Number', 'Product', 'From', 'To', 'Reason', 'Date']],
      body: tableData,
      styles: { fontSize: 10 },
      columnStyles: { 0: { cellWidth: 35 }, 1: { cellWidth: 40 } },
    });

    doc.save(`check-in-out-${format(new Date(), 'yyyy-MM-dd')}.pdf`);
  };

  if (view === 'scanner') {
    return (
      <div>
        <Button onClick={() => setView('list')} variant="outline" className="mb-4">
          ← Back to Records
        </Button>
        <CheckInOutManager
          defaultLocation="warehouse"
          showOrderFulfillment={true}
          title="Item Scanner - Check-In / Check-Out"
        />
      </div>
    );
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
          <TrendingUp className="w-5 h-5 md:w-6 md:h-6" />
          Check-In / Check-Out Records
        </h1>
        <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
          <Button onClick={() => setView('scanner')} size="lg" className="w-full sm:w-auto">
            <Package className="w-4 h-4 mr-2" />
            Scanner
          </Button>
          <Button onClick={exportToPDF} variant="outline" size="lg" disabled={filteredItems.length === 0} className="w-full sm:w-auto">
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Filters</span>
            {(searchTerm || dateFrom !== subDays(new Date(), 30).toISOString().split('T')[0]) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setDateFrom(subDays(new Date(), 30).toISOString().split('T')[0]);
                  setDateTo(new Date().toISOString().split('T')[0]);
                  setCurrentPage(1);
                }}
              >
                <X className="w-4 h-4 mr-2" />
                Clear Filters
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                placeholder="Serial #, Barcode, or Product..."
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">From Date</label>
              <Input type="date" value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">To Date</label>
              <Input type="date" value={dateTo} onChange={e => setDateTo(e.target.value)} />
            </div>
          </div>
        </CardContent>
      </Card>

      <LocalErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle>Records ({filteredItems.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading records...</div>
            ) : paginatedItems.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No records found</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b">
                      <tr>
                        <th className="text-left py-2 px-3">Serial Number</th>
                        <th className="text-left py-2 px-3">Product</th>
                        <th className="text-left py-2 px-3">From → To</th>
                        <th className="text-left py-2 px-3">Reason</th>
                        <th className="text-left py-2 px-3">Date</th>
                        <th className="text-left py-2 px-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(paginatedItems || []).map(item => (
                        <tr key={item?.id} className="border-b hover:bg-gray-50 cursor-pointer">
                          <td className="py-3 px-3">{item?.serialized_item?.serial_number || 'N/A'}</td>
                          <td className="py-3 px-3">{item?.serialized_item?.product?.name || 'N/A'}</td>
                          <td className="py-3 px-3">
                            <span className="text-xs">
                              {item?.from_location ? item.from_location.replace('_', ' ').toUpperCase() : 'N/A'} →{' '}
                              {item?.to_location ? item.to_location.replace('_', ' ').toUpperCase() : 'N/A'}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                              {item?.transfer_reason ? item.transfer_reason.replace('_', ' ').toUpperCase() : 'N/A'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-xs">{safeFormatDate(item?.timestamp)}</td>
                          <td className="py-3 px-3">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedHistory(item)}
                              className="mr-2"
                            >
                              View
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setDeleteConfirm(item?.id || null)}
                              className="text-red-600 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {totalPages > 1 && (
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      Showing {(currentPage - 1) * itemsPerPage + 1}-{Math.min(currentPage * itemsPerPage, filteredItems.length)} of {filteredItems.length}
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </Button>
                      <span className="flex items-center px-3 text-sm">
                        Page {currentPage} of {totalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </LocalErrorBoundary>

      {/* Detail Panel */}
      <Dialog open={!!selectedHistory} onOpenChange={() => setSelectedHistory(null)}>
        <DialogContent className="max-w-2xl">
          <LocalErrorBoundary>
            <DialogHeader>
              <DialogTitle>Check-In/Check-Out Details</DialogTitle>
            </DialogHeader>

            {selectedHistory && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 py-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Serial Number</p>
                    <p className="font-mono text-sm">{selectedHistory.serialized_item?.serial_number || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Barcode</p>
                    <p className="font-mono text-sm">{selectedHistory.serialized_item?.barcode || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Product</p>
                    <p className="text-sm">{selectedHistory.serialized_item?.product?.name || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Item Status</p>
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      {selectedHistory.serialized_item?.status ? selectedHistory.serialized_item.status.replace('_', ' ').toUpperCase() : 'N/A'}
                    </span>
                  </div>
                  <div className="col-span-2">
                    <p className="text-xs text-gray-500 mb-1">Transfer</p>
                    <p className="text-sm">
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-xs">
                        {selectedHistory.from_location ? selectedHistory.from_location.replace('_', ' ').toUpperCase() : 'INITIAL'}
                      </span>
                      {' → '}
                      <span className="bg-green-100 text-green-800 px-2 py-1 rounded text-xs">
                        {selectedHistory.to_location ? selectedHistory.to_location.replace('_', ' ').toUpperCase() : 'N/A'}
                      </span>
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Transfer Reason</p>
                    <span className="text-sm bg-indigo-100 text-indigo-800 px-2 py-1 rounded">
                      {selectedHistory.transfer_reason ? selectedHistory.transfer_reason.replace('_', ' ').toUpperCase() : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Date & Time</p>
                    <p className="text-sm">{safeFormatDate(selectedHistory.timestamp, true)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">From Holder</p>
                    <p className="text-sm">{selectedHistory.from_holder?.full_name || selectedHistory.from_holder?.username || 'System'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">To Holder</p>
                    <p className="text-sm">{selectedHistory.to_holder?.full_name || selectedHistory.to_holder?.username || 'N/A'}</p>
                  </div>
                  {selectedHistory.notes && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-500 mb-1">Notes</p>
                      <p className="text-sm">{selectedHistory.notes}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedHistory(null)}>
                Close
              </Button>
              <Button
                variant="destructive"
                onClick={() => {
                  setDeleteConfirm(selectedHistory?.id || null);
                  setSelectedHistory(null);
                }}
              >
                Delete Record
              </Button>
            </DialogFooter>
          </LocalErrorBoundary>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Record?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-600">This action cannot be undone.</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirm(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleteLoading}>
              {deleteLoading ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
