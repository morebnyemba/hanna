'use client';

import { useEffect, useState } from 'react';
import { FiShoppingCart, FiPackage, FiMapPin, FiUser, FiCalendar, FiSearch, FiFilter, FiCheckCircle, FiClock, FiTruck } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

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
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('all');

  useEffect(() => {
    const fetchOrders = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await apiClient.get('/crm-api/orders/');
        setOrders(response.data.results || response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch orders.');
      } finally {
        setLoading(false);
      }
    };

    fetchOrders();
  }, []);

  const filteredOrders = orders.filter(order => {
    const matchesSearch = 
      order.order_number?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customer?.full_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStage = stageFilter === 'all' || order.stage === stageFilter;
    
    return matchesSearch && matchesStage;
  });

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
        <div className="flex gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <Input
              placeholder="Search orders..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
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
                <div className="space-y-4">
                  {filteredOrders.map((order) => {
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
    </main>
  );
}
