'use client';

import { useEffect, useState, Component, ReactNode } from 'react';
import { Package, Plus, Edit2, Trash2, Download, Filter, X, AlertCircle } from 'lucide-react';
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

interface Product {
  id: number;
  name: string;
  sku: string;
  price: string;
  category: {
    id: number;
    name: string;
  };
  is_active: boolean;
  description?: string;
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

// Main Component
export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [categories, setCategories] = useState<Array<{ id: number; name: string }>>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const filteredProducts = products.filter(product => {
    const matchesSearch =
      product?.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product?.sku?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesCategory = !categoryFilter || product?.category?.id === Number(categoryFilter);
    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'active' && product?.is_active) ||
      (statusFilter === 'inactive' && !product?.is_active);

    return matchesSearch && matchesCategory && matchesStatus;
  });

  const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
  const paginatedProducts = filteredProducts.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      let url: string | null = '/crm-api/products/products/?ordering=-id';
      const all: Product[] = [];

      while (url) {
        const resp = await apiClient.get<PaginatedResponse<Product> | Product[]>(url);
        const pageItems = Array.isArray(resp.data) ? resp.data : resp.data.results || [];
        all.push(...pageItems);
        url = toRelative(Array.isArray(resp.data) ? null : (resp.data as PaginatedResponse<Product>).next);
      }

      setProducts(all);
      setCurrentPage(1);
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to load products'));
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const resp = await apiClient.get<PaginatedResponse<{ id: number; name: string }>>(
        '/crm-api/products/categories/?ordering=name'
      );
      const items = Array.isArray(resp.data) ? resp.data : resp.data.results || [];
      setCategories(items);
    } catch (e) {
      console.error('Failed to load categories:', e);
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, []);

  const handleDelete = async () => {
    if (!deleteConfirm) return;
    setDeleteLoading(true);
    try {
      await apiClient.delete(`/crm-api/products/products/${deleteConfirm}/`);
      setProducts(products.filter(p => p.id !== deleteConfirm));
      setDeleteConfirm(null);
      setSelectedProduct(null);
    } catch (e) {
      setError(extractErrorMessage(e, 'Failed to delete product'));
    } finally {
      setDeleteLoading(false);
    }
  };

  const exportToPDF = () => {
    const doc = new jsPDF();
    const tableData = filteredProducts.map(product => [
      product?.name || 'N/A',
      product?.sku || 'N/A',
      product?.category?.name || 'N/A',
      `$${product?.price || '0'}`,
      product?.is_active ? 'Active' : 'Inactive',
    ]);

    autoTable(doc, {
      head: [['Product Name', 'SKU', 'Category', 'Price', 'Status']],
      body: tableData,
      styles: { fontSize: 10 },
      columnStyles: { 0: { cellWidth: 50 }, 1: { cellWidth: 30 } },
    });

    doc.save(`products-${format(new Date(), 'yyyy-MM-dd')}.pdf`);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Package className="w-6 h-6" />
          Products
        </h1>
        <div className="flex gap-2 w-full sm:w-auto">
          <Link href="/admin/products/create" className="flex-1 sm:flex-none">
            <Button className="w-full sm:w-auto">
              <Plus className="w-4 h-4 mr-2" />
              Create Product
            </Button>
          </Link>
          <Button onClick={exportToPDF} variant="outline" disabled={filteredProducts.length === 0}>
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
            {(searchTerm || categoryFilter || statusFilter !== 'all') && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchTerm('');
                  setCategoryFilter('');
                  setStatusFilter('all');
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
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                placeholder="Product name or SKU..."
                value={searchTerm}
                onChange={e => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Category</label>
              <select
                value={categoryFilter}
                onChange={e => {
                  setCategoryFilter(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Categories</option>
                {(categories || []).map(cat => (
                  <option key={cat?.id} value={cat?.id}>
                    {cat?.name || 'N/A'}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <select
                value={statusFilter}
                onChange={e => {
                  setStatusFilter(e.target.value as 'all' | 'active' | 'inactive');
                  setCurrentPage(1);
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">All</option>
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <LocalErrorBoundary>
        <Card>
          <CardHeader>
            <CardTitle>Products ({filteredProducts.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-gray-500">Loading products...</div>
            ) : paginatedProducts.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No products found</div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="border-b">
                      <tr>
                        <th className="text-left py-2 px-3">Product</th>
                        <th className="text-left py-2 px-3">SKU</th>
                        <th className="text-left py-2 px-3">Category</th>
                        <th className="text-left py-2 px-3">Price</th>
                        <th className="text-left py-2 px-3">Status</th>
                        <th className="text-left py-2 px-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(paginatedProducts || []).map(product => (
                        <tr key={product?.id} className="border-b hover:bg-gray-50">
                          <td className="py-3 px-3 font-medium">{product?.name || 'N/A'}</td>
                          <td className="py-3 px-3 font-mono text-xs">{product?.sku || 'N/A'}</td>
                          <td className="py-3 px-3 text-xs">{product?.category?.name || 'N/A'}</td>
                          <td className="py-3 px-3">${product?.price || '0'}</td>
                          <td className="py-3 px-3">
                            <span
                              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                product?.is_active
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {product?.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td className="py-3 px-3">
                            <div className="flex gap-2">
                              <Link href={`/admin/products/${product?.id}`}>
                                <Button variant="outline" size="sm">
                                  <Edit2 className="w-4 h-4" />
                                </Button>
                              </Link>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setDeleteConfirm(product?.id || null)}
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
                      Showing {(currentPage - 1) * itemsPerPage + 1}-{Math.min(currentPage * itemsPerPage, filteredProducts.length)} of {filteredProducts.length}
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

      {/* Delete Confirmation */}
      <Dialog open={!!deleteConfirm} onOpenChange={() => setDeleteConfirm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Product?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-gray-600">
            This action cannot be undone. The product will be permanently deleted.
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
