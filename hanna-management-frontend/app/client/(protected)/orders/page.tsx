"use client";
import { useEffect, useState } from 'react';
import apiClient from '@/app/lib/apiClient';
import { FiRefreshCw, FiEye } from 'react-icons/fi';
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

export default function ClientOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stageFilter, setStageFilter] = useState('all');
  const [paymentFilter, setPaymentFilter] = useState('all');
  const [detailDialog, setDetailDialog] = useState(false);
  const [selectedOrderDetail, setSelectedOrderDetail] = useState<OrderDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadOrders = async () => {
    setLoading(true); setError(null);
    try {
      const res = await apiClient.get('/crm-api/orders/my/');
      setOrders(res.data);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || 'Failed to load orders');
    } finally { setLoading(false); }
  };

  const loadOrderDetail = async (orderId: string) => {
    setDetailLoading(true);
    try {
      const res = await apiClient.get(`/crm-api/orders/${orderId}/fulfillment-status/`);
      setSelectedOrderDetail(res.data);
      setDetailDialog(true);
    } catch (e: unknown) {
      const err = e as { response?: { data?: { error?: string } } };
      setError(err.response?.data?.error || 'Failed to load order details');
    } finally { setDetailLoading(false); }
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">My Orders</h1>
        <Button variant="outline" onClick={loadOrders} disabled={loading} className="flex items-center gap-2">
          <FiRefreshCw className={loading ? 'animate-spin' : ''} /> Refresh
        </Button>
      </div>

      <div className="flex gap-4 flex-wrap">
        <div>
          <label className="text-xs font-medium text-gray-600">Stage</label>
          <select
            className="mt-1 border rounded px-3 py-2 text-sm"
            value={stageFilter}
            onChange={e => setStageFilter(e.target.value)}
          >
            <option value="all">All Stages</option>
            {uniqueStages.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-medium text-gray-600">Payment</label>
          <select
            className="mt-1 border rounded px-3 py-2 text-sm"
            value={paymentFilter}
            onChange={e => setPaymentFilter(e.target.value)}
          >
            <option value="all">All Payments</option>
            {uniquePaymentStatuses.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded bg-red-50 text-red-700 text-sm border border-red-200">{error}</div>
      )}

      {!loading && !error && filteredOrders.length === 0 && (
        <p className="text-sm text-gray-500">No orders found.</p>
      )}

      {filteredOrders.map(order => (
        <Card key={order.id} className="border shadow-sm">
          <CardHeader>
            <CardTitle className="flex justify-between items-center">
              <span>{order.order_number || order.name || 'Order'}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-gray-500">{new Date(order.created_at).toLocaleDateString()}</span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => loadOrderDetail(order.id)}
                  disabled={detailLoading}
                  className="flex items-center gap-1"
                >
                  <FiEye className="w-4 h-4" /> Details
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
              <div><span className="font-semibold">Stage:</span> {order.stage_display || order.stage}</div>
              <div><span className="font-semibold">Payment:</span> {order.payment_status_display || order.payment_status}</div>
              <div><span className="font-semibold">Total:</span> {order.amount ? `${order.amount} ${order.currency}` : '—'}</div>
              <div><span className="font-semibold">Fulfillment:</span> {overallFulfillment(order)}%</div>
            </div>
            <div className="space-y-3">
              {order.items.map(item => (
                <div key={item.id} className="p-3 border rounded bg-white">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{item.product_name}</span>
                    <span className="text-gray-600">{item.units_assigned}/{item.quantity} assigned</span>
                  </div>
                  <div className="mt-2 h-2 bg-gray-200 rounded overflow-hidden">
                    <div
                      className={`h-full ${item.is_fully_assigned ? 'bg-green-500' : 'bg-blue-500'}`}
                      style={{ width: `${item.fulfillment_percentage}%` }}
                    />
                  </div>
                  <div className="mt-1 text-xs text-gray-500">SKU: {item.product_sku}</div>
                  {item.is_fully_assigned && (
                    <div className="mt-2 text-xs text-green-600 font-medium">All units assigned ✔</div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Order Detail Dialog */}
      <Dialog open={detailDialog} onOpenChange={setDetailDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Order Details: {selectedOrderDetail?.order_number}</DialogTitle>
          </DialogHeader>
          {selectedOrderDetail && (
            <div className="space-y-4">
              <div className="text-sm">
                <span className="font-semibold">Customer:</span> {selectedOrderDetail.customer || 'N/A'}
              </div>
              <div className="space-y-3">
                <h3 className="font-semibold text-sm">Items</h3>
                {selectedOrderDetail.items.map(item => (
                  <div key={item.id} className="p-4 border rounded bg-gray-50">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <div className="font-medium text-sm">{item.product_name}</div>
                        <div className="text-xs text-gray-500">SKU: {item.product_sku}</div>
                      </div>
                      <div className="text-sm text-gray-600">
                        {item.units_assigned}/{item.quantity_ordered} assigned
                      </div>
                    </div>
                    {item.is_fully_assigned && item.assigned_serial_numbers.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <div className="text-xs font-semibold text-gray-700 mb-2">Assigned Serial Numbers:</div>
                        <div className="flex flex-wrap gap-2">
                          {item.assigned_serial_numbers.map((sn, idx) => (
                            <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-mono">
                              {sn}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {!item.is_fully_assigned && (
                      <div className="mt-2 text-xs text-amber-600">
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
    </div>
  );
}
