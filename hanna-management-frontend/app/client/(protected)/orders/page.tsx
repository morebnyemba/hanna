"use client";
import { useEffect, useState } from 'react';
import apiClient from '@/app/lib/apiClient';
import { FiRefreshCw, FiEye, FiAlertCircle, FiCheckCircle, FiPackage, FiFilter } from 'react-icons/fi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

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
  name?: string;
  stage: string;
  stage_display?: string;
  payment_status: string;
  payment_status_display?: string;
  amount?: string;
  currency: string;
  items: OrderItem[];
  created_at: string;
}

interface OrderItemDetail {
  id: number;
  product_sku: string;
  product_name: string;
  quantity_ordered: number;
  units_assigned: number;
  is_fully_assigned: boolean;
  assigned_serial_numbers: string[];
}

interface OrderDetail {
  order_id: string;
  order_number: string;
  customer: string | null;
  items: OrderItemDetail[];
}

// Helper function to format dates safely
const safeFormatDate = (dateString: string): string => {
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return 'Invalid Date';
  }
};

// Status badge component
const StageBadge = ({ stage }: { stage: string }) => {
  const stageStyles: { [key: string]: string } = {
    pending: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  };

  const style = stageStyles[stage?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${style}`}>
      {stage || 'Unknown'}
    </span>
  );
};

const PaymentBadge = ({ status }: { status: string }) => {
  const paymentStyles: { [key: string]: string } = {
    pending: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    refunded: 'bg-gray-100 text-gray-800',
  };

  const style = paymentStyles[status?.toLowerCase()] || 'bg-gray-100 text-gray-800';
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold ${style}`}>
      {status || 'Unknown'}
    </span>
  );
};

export default function ClientOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stageFilter, setStageFilter] = useState('all');
  const [paymentFilter, setPaymentFilter] = useState('all');
  const [detailDialog, setDetailDialog] = useState(false);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState<OrderDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadOrders = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/crm-api/orders/my/');
      setOrders(res.data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || 'Failed to load orders. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadOrderDetail = async (orderId: string) => {
    setDetailLoading(true);
    setError(null);
    try {
      const res = await apiClient.get(`/crm-api/orders/${orderId}/fulfillment-status/`);
      setSelectedOrderDetail(res.data);
      setDetailDialog(true);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || 'Failed to load order details. Please try again.');
    } finally {
      setDetailLoading(false);
    }
  };

  useEffect(() => { loadOrders(); }, []);

  const overallFulfillment = (o: Order) => {
    if (!o.items.length) return 0;
    const totalQty = o.items.reduce((a, i) => a + i.quantity, 0);
    const totalAssigned = o.items.reduce((a, i) => a + i.units_assigned, 0);
    if (totalQty === 0) return 0;
    return Math.round((totalAssigned / totalQty) * 100);
  };

  const filteredOrders = orders.filter(o => {
    if (stageFilter !== 'all' && o.stage !== stageFilter) return false;
    if (paymentFilter !== 'all' && o.payment_status !== paymentFilter) return false;
    return true;
  });

  const uniqueStages = Array.from(new Set(orders.map(o => o.stage)));
  const uniquePaymentStatuses = Array.from(new Set(orders.map(o => o.payment_status)));

  return (
    <main className="flex-1 p-4 md:p-8 overflow-y-auto">
      <div className="mb-4 md:mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2 flex items-center">
          <FiPackage className="mr-3 w-6 h-6 md:w-8 md:h-8" />
          My Orders
        </h1>
        <p className="text-sm md:text-base text-gray-600">Track and manage your orders</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 md:mb-6 p-3 md:p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg flex items-start md:items-center">
          <FiAlertCircle className="w-5 h-5 mr-2 shrink-0 mt-0.5 md:mt-0" />
          <span className="text-sm md:text-base">{error}</span>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-sm md:text-base text-gray-600">Loading your orders...</p>
          </div>
        </div>
      )}

      {/* Controls */}
      {!loading && (
        <>
          <div className="mb-6 flex flex-col sm:flex-row gap-3 items-stretch sm:items-center">
            <div className="flex-1 flex flex-col sm:flex-row gap-3">
              <div className="flex-1">
                <label className="text-xs md:text-sm font-medium text-gray-700 mb-2 flex items-center">
                  <FiFilter className="w-4 h-4 mr-2" />
                  Stage
                </label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={stageFilter}
                  onChange={e => setStageFilter(e.target.value)}
                >
                  <option value="all">All Stages</option>
                  {uniqueStages.map(s => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex-1">
                <label className="text-xs md:text-sm font-medium text-gray-700 block mb-2">Payment</label>
                <select
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={paymentFilter}
                  onChange={e => setPaymentFilter(e.target.value)}
                >
                  <option value="all">All Payments</option>
                  {uniquePaymentStatuses.map(p => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <Button
              variant="outline"
              onClick={loadOrders}
              disabled={loading}
              className="flex items-center justify-center gap-2 h-10 sm:h-auto"
            >
              <FiRefreshCw className={loading ? 'animate-spin' : ''} />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
          </div>

          {/* Empty State */}
          {!error && filteredOrders.length === 0 && (
            <div className="text-center py-12">
              <FiPackage className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-sm md:text-base text-gray-600">No orders found.</p>
            </div>
          )}

          {/* Orders List */}
          <div className="space-y-4 md:space-y-6">
            {filteredOrders.map(order => {
              const fulfillment = overallFulfillment(order);
              return (
                <Card key={order.id} className="border shadow-sm hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <CardTitle className="text-lg md:text-xl line-clamp-none">
                          {order.order_number || order.name || 'Order'}
                        </CardTitle>
                        <p className="text-xs md:text-sm text-gray-600 mt-2">
                          {safeFormatDate(order.created_at)}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => loadOrderDetail(order.id)}
                        disabled={detailLoading}
                        className="flex items-center justify-center gap-2 w-full sm:w-auto"
                      >
                        <FiEye className="w-4 h-4" />
                        Details
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 md:gap-4">
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Stage</p>
                        <StageBadge stage={order.stage_display || order.stage} />
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Payment</p>
                        <PaymentBadge status={order.payment_status_display || order.payment_status} />
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Total</p>
                        <p className="text-sm md:text-base font-semibold">
                          {order.amount ? `${order.amount} ${order.currency}` : '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 mb-1">Fulfillment</p>
                        <p className="text-sm md:text-base font-semibold text-blue-600">{fulfillment}%</p>
                      </div>
                    </div>

                    {/* Items */}
                    <div className="space-y-3">
                      {order.items.map(item => (
                        <div
                          key={item.id}
                          className="p-3 md:p-4 border rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-2">
                            <p className="font-medium text-sm md:text-base overflow-hidden">{item.product_name}</p>
                            <span className="text-xs md:text-sm text-gray-600 whitespace-nowrap">
                              {item.units_assigned}/{item.quantity} assigned
                            </span>
                          </div>
                          <div className="mb-2 h-2 bg-gray-300 rounded overflow-hidden">
                            <div
                              className={`h-full transition-all ${
                                item.is_fully_assigned ? 'bg-green-500' : 'bg-blue-500'
                              }`}
                              style={{ width: `${item.fulfillment_percentage}%` }}
                            />
                          </div>
                          <p className="text-xs text-gray-600 mb-2">SKU: {item.product_sku}</p>
                          {item.is_fully_assigned && (
                            <div className="flex items-center text-xs text-green-600 font-medium">
                              <FiCheckCircle className="w-4 h-4 mr-1" />
                              All units assigned
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </>
      )}

      {/* Order Detail Dialog */}
      <Dialog open={detailDialog} onOpenChange={setDetailDialog}>
        <DialogContent className="max-w-[95vw] sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-lg md:text-xl">
              Order Details: {selectedOrderDetail?.order_number}
            </DialogTitle>
          </DialogHeader>
          {selectedOrderDetail && (
            <div className="space-y-4">
              <div className="text-sm md:text-base">
                <span className="font-semibold">Customer:</span> {selectedOrderDetail.customer || 'N/A'}
              </div>
              <div className="space-y-3">
                <h3 className="font-semibold text-sm md:text-base">Items</h3>
                {selectedOrderDetail.items.map(item => (
                  <div key={item.id} className="p-3 md:p-4 border rounded-lg bg-gray-50">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-3">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm md:text-base overflow-hidden">{item.product_name}</div>
                        <div className="text-xs text-gray-600">SKU: {item.product_sku}</div>
                      </div>
                      <div className="text-sm text-gray-600 whitespace-nowrap">
                        {item.units_assigned}/{item.quantity_ordered} assigned
                      </div>
                    </div>
                    {item.is_fully_assigned && item.assigned_serial_numbers.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <div className="text-xs font-semibold text-gray-700 mb-2">Assigned Serial Numbers:</div>
                        <div className="flex flex-wrap gap-2">
                          {item.assigned_serial_numbers.map((sn, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-mono break-all"
                            >
                              {sn}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {!item.is_fully_assigned && (
                      <div className="mt-2 text-xs text-amber-600 font-medium">
                        Awaiting {item.quantity_ordered - item.units_assigned} more unit(s)
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </main>
  );
}
