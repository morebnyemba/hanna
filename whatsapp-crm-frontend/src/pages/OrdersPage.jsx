
import React, { useEffect, useState } from 'react';
import { ordersApi } from '@/services/orders';
import { Button } from '@/components/ui/button';

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    ordersApi.list()
      .then(res => setOrders(res.data))
      .catch(() => setError('Failed to load orders.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Orders</h1>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-500">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full border text-sm">
          <thead>
            <tr>
              <th className="border px-2 py-1">Order #</th>
              <th className="border px-2 py-1">Name</th>
              <th className="border px-2 py-1">Stage</th>
              <th className="border px-2 py-1">Payment</th>
              <th className="border px-2 py-1">Amount</th>
              <th className="border px-2 py-1">Created</th>
            </tr>
          </thead>
          <tbody>
            {orders.map(order => (
              <tr key={order.id}>
                <td className="border px-2 py-1">{order.order_number}</td>
                <td className="border px-2 py-1">{order.name}</td>
                <td className="border px-2 py-1">{order.stage_display || order.stage}</td>
                <td className="border px-2 py-1">{order.payment_status_display || order.payment_status}</td>
                <td className="border px-2 py-1">{order.amount} {order.currency}</td>
                <td className="border px-2 py-1">{order.created_at?.slice(0,10)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
