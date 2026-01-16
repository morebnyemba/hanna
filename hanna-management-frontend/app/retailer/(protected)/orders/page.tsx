'use client';

import { useEffect, useState } from 'react';
import { FiShoppingCart, FiCalendar, FiDollarSign, FiPackage, FiEye } from 'react-icons/fi';
import { useAuthStore } from '@/app/store/authStore';
import Link from 'next/link';

interface Order {
  id: string;
  order_number: string;
  customer_name: string;
  customer_phone: string;
  total_amount: string;
  currency: string;
  status: string;
  solar_package_name: string | null;
  created_at: string;
  installation_address: string;
}

export default function RetailerOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { accessToken } = useAuthStore();

  useEffect(() => {
    const fetchOrders = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';
        const response = await fetch(`${apiUrl}/crm-api/users/retailer/orders/`, {
          headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch orders. Status: ${response.status}`);
        }

        const result = await response.json();
        setOrders(result.results || result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (accessToken) {
      fetchOrders();
    }
  }, [accessToken]);

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', text: 'Pending' },
      confirmed: { color: 'bg-blue-100 text-blue-800', text: 'Confirmed' },
      processing: { color: 'bg-purple-100 text-purple-800', text: 'Processing' },
      completed: { color: 'bg-green-100 text-green-800', text: 'Completed' },
      cancelled: { color: 'bg-red-100 text-red-800', text: 'Cancelled' },
    };

    const config = statusConfig[status] || statusConfig.pending;
    
    return (
      <span className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${config.color}`}>
        {config.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-64 mb-6"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-32 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 sm:p-6 lg:p-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p className="font-bold">Error</p>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <div className="mb-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
            <FiShoppingCart className="mr-3 h-8 w-8 text-blue-600" />
            My Orders
          </h1>
          <p className="mt-2 text-sm text-gray-700">
            View and track all your customer orders.
          </p>
        </div>
        <Link
          href="/retailer/solar-packages"
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg flex items-center transition-colors"
        >
          <FiPackage className="mr-2" />
          Create New Order
        </Link>
      </div>

      {orders.length === 0 ? (
        <div className="bg-white p-8 rounded-lg shadow text-center">
          <FiShoppingCart className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-semibold text-gray-900">No orders yet</h3>
          <p className="mt-1 text-sm text-gray-500">
            Start by creating your first customer order from the solar packages catalog.
          </p>
          <Link
            href="/retailer/solar-packages"
            className="mt-4 inline-flex items-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            <FiPackage className="mr-2" />
            Browse Solar Packages
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {orders.map((order) => (
            <div
              key={order.id}
              className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
                {/* Order Info */}
                <div className="flex-1 mb-4 lg:mb-0">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Order #{order.order_number}
                      </h3>
                      <p className="text-sm text-gray-600 mt-1">
                        Customer: {order.customer_name}
                      </p>
                      {order.solar_package_name && (
                        <p className="text-sm text-blue-600 mt-1 flex items-center">
                          <FiPackage className="mr-1" />
                          {order.solar_package_name}
                        </p>
                      )}
                    </div>
                    <div className="ml-4">
                      {getStatusBadge(order.status)}
                    </div>
                  </div>

                  <div className="mt-3 space-y-2">
                    <div className="flex items-center text-sm text-gray-600">
                      <FiCalendar className="mr-2 text-gray-400" />
                      {new Date(order.created_at).toLocaleDateString()} at {new Date(order.created_at).toLocaleTimeString()}
                    </div>
                    {order.installation_address && (
                      <div className="flex items-start text-sm text-gray-600">
                        <FiPackage className="mr-2 mt-1 text-gray-400 flex-shrink-0" />
                        <span>{order.installation_address}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Order Amount */}
                <div className="lg:ml-6 pt-4 lg:pt-0 border-t lg:border-t-0 lg:border-l lg:pl-6">
                  <div className="flex items-center justify-between lg:justify-start lg:flex-col lg:items-end gap-4">
                    <div>
                      <div className="text-sm text-gray-500">Order Total</div>
                      <div className="text-2xl font-bold text-gray-900 flex items-center mt-1">
                        <FiDollarSign className="h-5 w-5" />
                        {parseFloat(order.total_amount).toLocaleString()}
                        <span className="text-sm text-gray-600 ml-1">{order.currency}</span>
                      </div>
                    </div>
                    <button
                      className="text-blue-600 hover:text-blue-800 flex items-center text-sm font-medium"
                      onClick={() => alert('Order details view - to be implemented')}
                    >
                      <FiEye className="mr-1" />
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
