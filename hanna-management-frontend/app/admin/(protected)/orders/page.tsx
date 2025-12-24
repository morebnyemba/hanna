'use client';

import { useEffect, useState } from 'react';
import { FiShoppingCart, FiPackage, FiMapPin, FiUser, FiCalendar, FiSearch, FiFilter, FiCheckCircle, FiClock, FiTruck, FiDownload, FiEdit, FiTrash2, FiChevronLeft, FiChevronRight } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import DeleteConfirmationModal from '@/app/components/shared/DeleteConfirmationModal';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';

interface OrderItem {
  id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  units_assigned: number;
  is_fully_assigned: boolean;
  fulfillment_percentage: number;
}

interface Order {
  id: string;
  order_number: string;
  name: string | null;
  customer: {
    full_name: string;
    company: string | null;
  } | null;
  stage: string;
  stage_display: string;
  payment_status: string;
  payment_status_display: string;
  amount: string | null;
  currency: string;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

const stageColors: Record<string, string> = {
  prospecting: 'bg-gray-100 text-gray-800',
  qualification: 'bg-blue-100 text-blue-800',
  proposal: 'bg-purple-100 text-purple-800',
  negotiation: 'bg-yellow-100 text-yellow-800',
  closed_won: 'bg-green-100 text-green-800',
  closed_lost: 'bg-red-100 text-red-800',
};

const paymentStatusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  paid: 'bg-green-100 text-green-800',
  partially_paid: 'bg-blue-100 text-blue-800',
  refunded: 'bg-red-100 text-red-800',
  not_applicable: 'bg-gray-100 text-gray-800',
};

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [filteredOrders, setFilteredOrders] = useState<Order[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [orderToDelete, setOrderToDelete] = useState<Order | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingOrder, setEditingOrder] = useState<Order | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const itemsPerPage = 10;

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      setError(null);
      try {
        let url: string | null = '/crm-api/customer-data/orders/?ordering=-created_at';
        const all: Order[] = [] as any;
        while (url) {
          const response = await apiClient.get(url);
          const payload = response.data;
          const pageItems: Order[] = payload.results || payload;
          all.push(...pageItems);
          url = payload.next || null;
        }
        setOrders(all);
        setFilteredOrders(all);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch orders.');
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  useEffect(() => {
    let filtered = orders.filter(order => {
      const matchesSearch = 
        order.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        order.customer?.full_name?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStage = stageFilter === 'all' || order.stage === stageFilter;
      
      const orderDate = new Date(order.created_at);
      const matchesStartDate = !startDate || orderDate >= new Date(startDate);
      const matchesEndDate = !endDate || orderDate <= new Date(endDate);
      
      return matchesSearch && matchesStage && matchesStartDate && matchesEndDate;
    });
    
    setFilteredOrders(filtered);
    setCurrentPage(1);
  }, [searchTerm, stageFilter, startDate, endDate, orders]);

  // Pagination
  const totalPages = Math.ceil(filteredOrders.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentOrders = filteredOrders.slice(startIndex, endIndex);

  // PDF Export
  const handleExportPDF = () => {
    const doc = new jsPDF();
    
    doc.setFontSize(18);
    doc.text('Orders Report', 14, 22);
    
    doc.setFontSize(11);
    doc.text(`Generated: ${new Date().toLocaleDateString()}`, 14, 30);
    
    const tableData = filteredOrders.map(order => [
      order.order_number,
      order.customer?.full_name || 'Unknown',
      order.stage_display,
      order.amount ? `${order.currency} ${order.amount}` : '-',
      new Date(order.created_at).toLocaleDateString(),
    ]);
    
    autoTable(doc, {
      head: [['Order #', 'Customer', 'Stage', 'Amount', 'Date']],
      body: tableData,
      startY: 35,
      theme: 'grid',
      headStyles: { fillColor: [124, 58, 237] },
    });
    
    doc.save(`orders-${new Date().toISOString().split('T')[0]}.pdf`);
  };

  const handleDeleteClick = (order: Order) => {
    setOrderToDelete(order);
    setDeleteModalOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!orderToDelete) return;

    setIsDeleting(true);
    try {
      await apiClient.delete(`/crm-api/customer-data/orders/${orderToDelete.id}/`);
      setOrders(orders.filter(o => o.id !== orderToDelete.id));
      if (selectedOrder?.id === orderToDelete.id) {
        setSelectedOrder(null);
      }
      setDeleteModalOpen(false);
      setOrderToDelete(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteModalOpen(false);
    setOrderToDelete(null);
  };

  const handleEditClick = (order: Order) => {
    setEditingOrder(order);
    setEditModalOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!editingOrder) return;

    const formData = new FormData(e.currentTarget);
    
    try {
      const response = await apiClient.patch(`/crm-api/customer-data/orders/${editingOrder.id}/`, {
        stage: formData.get('stage'),
        payment_status: formData.get('payment_status'),
      });
      
      setOrders(orders.map(o => o.id === editingOrder.id ? response.data : o));
      if (selectedOrder?.id === editingOrder.id) {
        setSelectedOrder(response.data);
      }
      setEditModalOpen(false);
      setEditingOrder(null);
    } catch (err: any) {
      alert('Failed to update order: ' + (err.response?.data?.detail || err.message));
    }
  };

  const getOrderProgress = (order: Order) => {
    if (!order.items || order.items.length === 0) return 0;
    const totalItems = order.items.reduce((sum, item) => sum + item.quantity, 0);
    const assignedItems = order.items.reduce((sum, item) => sum + item.units_assigned, 0);
    return Math.round((assignedItems / totalItems) * 100);
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center gap-2">
          <FiShoppingCart className="w-6 h-6" /> Order Tracking
        </h1>
        <Button 
          onClick={handleExportPDF}
          className="bg-purple-600 hover:bg-purple-700 text-white flex items-center justify-center gap-2"
        >
          <FiDownload /> Export PDF
        </Button>
      </div>

      <div className="mb-6 flex flex-col lg:flex-row gap-4">
        <div className="relative flex-1">
          <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Search orders..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full sm:w-auto"
            placeholder="Start Date"
          />
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full sm:w-auto"
            placeholder="End Date"
          />
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="border rounded px-3 py-2 text-sm w-full sm:w-auto"
          >
            <option value="all">All Stages</option>
            <option value="prospecting">Prospecting</option>
            <option value="qualification">Qualification</option>
            <option value="proposal">Proposal</option>
            <option value="negotiation">Negotiation</option>
            <option value="closed_won">Closed Won</option>
            <option value="closed_lost">Closed Lost</option>
          </select>
        </div>
      </div>
      
      {error && <p className="text-center text-red-500 py-4">Error: {error}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Orders List */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiShoppingCart className="w-5 h-5" /> All Orders
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map(i => (
                    <div key={i} className="animate-pulse bg-gray-100 h-24 rounded-lg"></div>
                  ))}
                </div>
              ) : filteredOrders.length === 0 ? (
                <p className="text-gray-500 text-center py-8">No orders found.</p>
              ) : (
                <>
                  <div className="space-y-4">
                    {currentOrders.map((order) => {
                      const progress = getOrderProgress(order);
                      return (
                        <div
                          key={order.id}
                          className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors ${
                            selectedOrder?.id === order.id ? 'border-purple-500 bg-purple-50' : ''
                          }`}
                          onClick={() => setSelectedOrder(order)}
                        >
                          <div className="flex justify-between items-start">
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">#{order.order_number}</span>
                                {order.name && <span className="text-sm text-gray-500">- {order.name}</span>}
                              </div>
                              <div className="flex items-center gap-2 text-sm text-gray-600">
                                <FiUser className="w-4 h-4" />
                                <span>{order.customer?.full_name || 'Unknown Customer'}</span>
                              </div>
                              <div className="text-xs text-gray-500">
                                {order.amount && `${order.currency} ${order.amount}`}
                                {' • '}
                                {new Date(order.created_at).toLocaleDateString()}
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-2">
                              <div className="flex gap-2">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleEditClick(order);
                                  }}
                                  className="text-blue-600 hover:text-blue-800"
                                  title="Edit"
                                >
                                  <FiEdit className="w-4 h-4" />
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleDeleteClick(order);
                                  }}
                                  className="text-red-600 hover:text-red-800"
                                  title="Delete"
                                >
                                  <FiTrash2 className="w-4 h-4" />
                                </button>
                              </div>
                              <Badge className={stageColors[order.stage] || 'bg-gray-100'}>
                              {order.stage_display}
                            </Badge>
                            <Badge className={paymentStatusColors[order.payment_status] || 'bg-gray-100'} variant="outline">
                              {order.payment_status_display}
                            </Badge>
                          </div>
                        </div>
                        
                        {/* Fulfillment Progress */}
                        {order.items && order.items.length > 0 && (
                          <div className="mt-3">
                            <div className="flex items-center justify-between text-xs mb-1">
                              <span className="text-gray-600 flex items-center gap-1">
                                <FiTruck className="w-3 h-3" /> Dispatch Progress
                              </span>
                              <span className={progress === 100 ? 'text-green-600' : 'text-gray-600'}>
                                {progress}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${progress === 100 ? 'bg-green-500' : 'bg-blue-500'}`}
                                style={{ width: `${progress}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
                
                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex justify-center items-center gap-4 mt-6 pt-4 border-t">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="flex items-center gap-2 px-3 py-2 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100 rounded"
                    >
                      <FiChevronLeft /> Previous
                    </button>
                    <span className="text-sm text-gray-600">
                      Page {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
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

        {/* Order Detail */}
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FiPackage className="w-5 h-5" /> Order Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {!selectedOrder ? (
                <p className="text-gray-500 text-center py-8">Select an order to view details</p>
              ) : (
                <div className="space-y-4">
                  <div>
                    <p className="text-sm text-gray-500">Order Number</p>
                    <p className="font-medium">#{selectedOrder.order_number}</p>
                  </div>

                  <div>
                    <p className="text-sm text-gray-500">Customer</p>
                    <p className="font-medium">{selectedOrder.customer?.full_name || 'Unknown'}</p>
                    {selectedOrder.customer?.company && (
                      <p className="text-sm text-gray-600">{selectedOrder.customer.company}</p>
                    )}
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    <Badge className={stageColors[selectedOrder.stage] || 'bg-gray-100'}>
                      {selectedOrder.stage_display}
                    </Badge>
                    <Badge className={paymentStatusColors[selectedOrder.payment_status] || 'bg-gray-100'}>
                      {selectedOrder.payment_status_display}
                    </Badge>
                  </div>

                  {selectedOrder.amount && (
                    <div>
                      <p className="text-sm text-gray-500">Amount</p>
                      <p className="text-lg font-bold">{selectedOrder.currency} {selectedOrder.amount}</p>
                    </div>
                  )}

                  <div className="pt-4 border-t">
                    <p className="text-sm font-medium mb-2 flex items-center gap-2">
                      <FiPackage className="w-4 h-4" /> Order Items
                    </p>
                    {selectedOrder.items && selectedOrder.items.length > 0 ? (
                      <div className="space-y-3">
                        {selectedOrder.items.map((item) => (
                          <div key={item.id} className="bg-gray-50 p-3 rounded">
                            <div className="flex justify-between items-start">
                              <div>
                                <p className="font-medium text-sm">{item.product_name}</p>
                                <p className="text-xs text-gray-500">SKU: {item.product_sku}</p>
                              </div>
                              <span className="text-sm">x{item.quantity}</span>
                            </div>
                            <div className="mt-2">
                              <div className="flex items-center justify-between text-xs mb-1">
                                <span className="text-gray-600">
                                  {item.units_assigned}/{item.quantity} dispatched
                                </span>
                                {item.is_fully_assigned ? (
                                  <FiCheckCircle className="w-3 h-3 text-green-500" />
                                ) : (
                                  <FiClock className="w-3 h-3 text-yellow-500" />
                                )}
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1.5">
                                <div
                                  className={`h-1.5 rounded-full ${item.is_fully_assigned ? 'bg-green-500' : 'bg-blue-500'}`}
                                  style={{ width: `${item.fulfillment_percentage}%` }}
                                />
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-sm">No items in this order</p>
                    )}
                  </div>

                  <div className="text-xs text-gray-400 pt-2 border-t">
                    <p>Created: {new Date(selectedOrder.created_at).toLocaleString()}</p>
                    <p>Updated: {new Date(selectedOrder.updated_at).toLocaleString()}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Edit Order Modal */}
      <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Order #{editingOrder?.order_number}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEditSubmit} className="space-y-4">
            <div>
              <Label htmlFor="stage">Stage</Label>
              <select
                id="stage"
                name="stage"
                defaultValue={editingOrder?.stage}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                required
              >
                <option value="prospecting">Prospecting</option>
                <option value="qualification">Qualification</option>
                <option value="proposal">Proposal</option>
                <option value="negotiation">Negotiation</option>
                <option value="closed_won">Closed Won</option>
                <option value="closed_lost">Closed Lost</option>
              </select>
            </div>
            <div>
              <Label htmlFor="payment_status">Payment Status</Label>
              <select
                id="payment_status"
                name="payment_status"
                defaultValue={editingOrder?.payment_status}
                className="w-full mt-1 px-3 py-2 border rounded-md"
                required
              >
                <option value="pending">Pending</option>
                <option value="partial">Partial</option>
                <option value="paid">Paid</option>
                <option value="failed">Failed</option>
                <option value="refunded">Refunded</option>
              </select>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <Button type="button" variant="outline" onClick={() => setEditModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-purple-600 hover:bg-purple-700">
                Save Changes
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModalOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Order"
        message={`Are you sure you want to delete Order #${orderToDelete?.order_number}? This action cannot be undone.`}
        isDeleting={isDeleting}
      />
    </main>
  );
}
