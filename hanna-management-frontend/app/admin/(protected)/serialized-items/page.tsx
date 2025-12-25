'use client';

import { useEffect, useState, Component, ReactNode } from 'react';
import { Archive, Plus, Edit2, Trash2, Download, Filter, X, AlertCircle } from 'lucide-react';
import Link from 'next/link';
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
import apiClient from '@/app/lib/apiClient';
import { extractErrorMessage } from '@/app/lib/apiUtils';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { format } from 'date-fns';

// Interfaces
interface PaginatedResponse<T> {
  results: T[];
  next: string | null;
  previous?: string | null;
  count?: number;
}

interface SerializedItem {
  id: number;
  serial_number: string;
  barcode?: string;
  status: string;
  current_location: string;
  product: {
    id: number;
    name: string;
    sku: string;
  };
  current_holder?: {
    id: number;
    username: string;
    full_name: string;
  } | null;
  created_at?: string;
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
function toRelative(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    return parsed.pathname + parsed.search;
  } catch {
    return url;
  }
}

function safeFormatDate(value: string | Date | undefined | null): string {
  try {
    if (!value) return 'N/A';
    const date = typeof value === 'string' ? new Date(value) : value;
    if (isNaN(date.getTime())) return 'Invalid Date';
    return format(date, 'MMM dd, yyyy');
  } catch {
    return 'Invalid Date';
  }
}

// Main Component
export default function SerializedItemsPage() {
  const [items, setItems] = useState<SerializedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [locationFilter, setLocationFilter] = useState<string>('');
  const [selectedItem, setSelectedItem] = useState<SerializedItem | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const filteredItems = items.filter(item => {
    const matchesSearch =
      item?.serial_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item?.barcode?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item?.product?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item?.product?.sku?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = !statusFilter || item?.status === statusFilter;
    const matchesLocation = !locationFilter || item?.current_location === locationFilter;

    return matchesSearch && matchesStatus && matchesLocation;
  });

  const totalPages = Math.ceil(filteredItems.length / itemsPerPage);
  const paginatedItems = filteredItems.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const fetchItems = async () => {
    setLoading(true);
    setError(null);
    try {
      let url: string | null = '/crm-api/products/serialized-items/?ordering=-id';
      const all: SerializedItem[] = [];

      while (url) {
        const resp = await apiClient.get<PaginatedResponse<SerializedItem> | SerializedItem[]>(url);
        const pageItems = Array.isArray(resp.data) ? resp.data : resp.data.results || [];
        all.push(...pageItems);
        url = toRelative(Array.isArray(resp.data) ? null : (resp.data as PaginatedResponse<SerializedItem>).next);
      }

      setItems(all);
      setCurrentPage(1);
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to load serialized items'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await apiClient.delete(`/crm-api/products/serialized-items/${deleteConfirm}/`);
      setItems(items.filter(i => i.id !== deleteConfirm));
      setDeleteConfirm(null);
      setSelectedItem(null);
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to delete item'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    const tableData = filteredItems.map(item => [
      item?.serial_number || 'N/A',
      item?.product?.name || 'N/A',
      item?.product?.sku || 'N/A',
      item?.status ? item.status.replace('_', ' ').toUpperCase() : 'N/A',
      item?.current_location ? item.current_location.replace('_', ' ').toUpperCase() : 'N/A',
    ]);

    autoTable(doc, {
      head: [['Serial #', 'Product', 'SKU', 'Status', 'Location']],
      body: tableData,
      styles: { fontSize: 10 },
      columnStyles: { 0: { cellWidth: 35 }, 1: { cellWidth: 50 } },
    });

    doc.save(`serialized-items-${format(new Date(), 'yyyy-MM-dd')}.pdf`);
  };

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      in_stock: 'bg-green-100 text-green-800',
      sold: 'bg-purple-100 text-purple-800',
      in_repair: 'bg-yellow-100 text-yellow-800',
      returned: 'bg-orange-100 text-orange-800',
      decommissioned: 'bg-gray-100 text-gray-800',
      in_transit: 'bg-blue-100 text-blue-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Archive className="w-6 h-6" />
          Serialized Items
        </h1>
        <div className="flex gap-2 w-full sm:w-auto">
          <Link href="/admin/serialized-items/create" className="flex-1 sm:flex-none">
            <Button className="w-full sm:w-auto">
              <Plus className="w-4 h-4 mr-2" />
              Create Item
            </Button>
          </Link>
          <Button onClick={exportToPDF} variant="outline" disabled={filteredItems.length === 0}>
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
            {(searchTerm || statusFilter || locationFilter) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setStatusFilter('');
                  setLocationFilter('');
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
                placeholder="Serial #, Barcode, Product, or SKU..."
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <select
                value={statusFilter}
                onChange={e => {
                  setStatusFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Statuses</option>
                <option value="in_stock">In Stock</option>
                <option value="sold">Sold</option>
                <option value="in_repair">In Repair</option>
                <option value="in_transit">In Transit</option>
                <option value="returned">Returned</option>
                <option value="decommissioned">Decommissioned</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Location</label>
              <select
                value={locationFilter}
                onChange={e => {
                  setLocationFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Locations</option>
                <option value="warehouse">Warehouse</option>
                <option value="customer">Customer</option>
                <option value="technician">Technician</option>
                <option value="manufacturer">Manufacturer</option>
                <option value="in_transit">In Transit</option>
                <option value="retail">Retail</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <LocalErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle>Items ({filteredItems.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading items...</div>
            ) : paginatedItems.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No items found</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b">
                      <tr>
                        <th className="text-left py-2 px-3">Serial Number</th>
                        <th className="text-left py-2 px-3">Product</th>
                        <th className="text-left py-2 px-3">Status</th>
                        <th className="text-left py-2 px-3">Location</th>
                        <th className="text-left py-2 px-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(paginatedItems || []).map(item => (
                        <tr
                          key={item?.id}
                          className="border-b hover:bg-gray-50 cursor-pointer"
                          onClick={() => setSelectedItem(item)}
                        >
                          <td className="py-3 px-3 font-mono text-xs">{item?.serial_number || 'N/A'}</td>
                          <td className="py-3 px-3">
                            <div className="flex flex-col">
                              <span className="font-medium">{item?.product?.name || 'N/A'}</span>
                              <span className="text-xs text-gray-500">{item?.product?.sku || ''}</span>
                            </div>
                          </td>
                          <td className="py-3 px-3">
                            <span
                              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(
                                item?.status || ''
                              )}`}
                            >
                              {item?.status ? item.status.replace('_', ' ').toUpperCase() : 'N/A'}
                            </span>
                          </td>
                          <td className="py-3 px-3 text-xs">
                            {item?.current_location ? item.current_location.replace('_', ' ').toUpperCase() : 'N/A'}
                          </td>
                          <td className="py-3 px-3">
                            <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                              {item?.id ? (
                                <Link
                                  href={`/admin/serialized-items/${item.id}`}
                                  className="inline-flex items-center gap-2 px-2 py-1 border rounded-md text-sm hover:bg-gray-50"
                                >
                                  <Edit2 className="w-4 h-4" />
                                  Edit
                                </Link>
                              ) : (
                                <span className="inline-flex items-center gap-2 px-2 py-1 border rounded-md text-sm text-gray-400 cursor-not-allowed">
                                  <Edit2 className="w-4 h-4" />
                                  Edit
                                </span>
                              )}
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setDeleteConfirm(item?.id || null);
                                }}
                                className="text-red-600 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
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
      <Dialog open={!!selectedItem} onOpenChange={() => setSelectedItem(null)}>
        <DialogContent className="max-w-2xl">
          <LocalErrorBoundary>
            <DialogHeader>
              <DialogTitle>Serialized Item Details</DialogTitle>
            </DialogHeader>

            {selectedItem && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 py-4">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Serial Number</p>
                    <p className="font-mono text-sm">{selectedItem.serial_number || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Barcode</p>
                    <p className="font-mono text-sm">{selectedItem.barcode || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Product</p>
                    <p className="text-sm">{selectedItem.product?.name || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">SKU</p>
                    <p className="text-sm">{selectedItem.product?.sku || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Status</p>
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeColor(
                        selectedItem.status
                      )}`}
                    >
                      {selectedItem.status ? selectedItem.status.replace('_', ' ').toUpperCase() : 'N/A'}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Current Location</p>
                    <p className="text-sm">
                      {selectedItem.current_location ? selectedItem.current_location.replace('_', ' ').toUpperCase() : 'N/A'}
                    </p>
                  </div>
                  {selectedItem.current_holder && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-500 mb-1">Current Holder</p>
                      <p className="text-sm">
                        {selectedItem.current_holder.full_name || selectedItem.current_holder.username}
                      </p>
                    </div>
                  )}
                  {selectedItem.created_at && (
                    <div className="col-span-2">
                      <p className="text-xs text-gray-500 mb-1">Created</p>
                      <p className="text-sm">{safeFormatDate(selectedItem.created_at)}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            <DialogFooter>
              <Button variant="outline" onClick={() => setSelectedItem(null)}>
                Close
              </Button>
              {selectedItem?.id ? (
                <Link
                  href={`/admin/serialized-items/${selectedItem.id}`}
                  className="inline-flex items-center gap-2 px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700"
                >
                  <Edit2 className="w-4 h-4" />
                  Edit
                </Link>
              ) : (
                <span className="inline-flex items-center gap-2 px-3 py-2 bg-gray-200 text-gray-500 rounded-md cursor-not-allowed">
                  <Edit2 className="w-4 h-4" />
                  Edit
                </span>
              )}
            </DialogFooter>
          </LocalErrorBoundary>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Serialized Item?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-600">
            This action cannot be undone. The item will be permanently deleted.
          </p>
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
