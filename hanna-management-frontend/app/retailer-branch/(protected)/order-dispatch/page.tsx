'use client';

import { useState } from 'react';
import { FiSearch, FiPackage, FiCheck, FiAlertCircle, FiCamera, FiTruck, FiClipboard } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import BarcodeScanner from '@/app/components/BarcodeScanner';

interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  units_assigned: number;
  is_fully_assigned: boolean;
  remaining: number;
}

interface Order {
  order_id: string;
  order_number: string;
  customer_name: string | null;
  payment_status: string;
  stage: string;
  items: OrderItem[];
  is_eligible_for_dispatch: boolean;
  dispatch_message: string;
}

interface DispatchResult {
  success: boolean;
  message: string;
  item?: {
    item_id: number;
    serial_number: string;
    barcode: string | null;
    product_name: string;
    order_item_id: number;
    units_assigned: number;
    quantity_ordered: number;
    is_fully_assigned: boolean;
    dispatch_timestamp: string;
  };
  order_fulfillment?: {
    order_number: string;
    items_remaining: number;
    total_items: number;
    all_dispatched: boolean;
  };
}

export default function OrderDispatchPage() {
  const [orderNumber, setOrderNumber] = useState('');
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [showScanner, setShowScanner] = useState(false);
  const [scanMode, setScanMode] = useState<'order' | 'item'>('order');
  const [selectedOrderItem, setSelectedOrderItem] = useState<OrderItem | null>(null);
  const [serialNumber, setSerialNumber] = useState('');
  const [notes, setNotes] = useState('');
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  const [dispatchedItems, setDispatchedItems] = useState<DispatchResult['item'][]>([]);

  // Verify order
  const handleVerifyOrder = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!orderNumber.trim()) return;
    
    setLoading(true);
    setResult(null);
    setOrder(null);
    setDispatchedItems([]);
    
    try {
      const response = await apiClient.get(`/crm-api/products/retailer-branch/order/verify/${encodeURIComponent(orderNumber)}/`);
      setOrder(response.data);
      if (!response.data.is_eligible_for_dispatch) {
        setResult({ success: false, message: response.data.dispatch_message });
      } else {
        setResult({ success: true, message: response.data.dispatch_message });
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
      setResult({
        success: false,
        message: error.response?.data?.error || error.message || 'Failed to verify order.'
      });
    } finally {
      setLoading(false);
    }
  };

  // Dispatch item
  const handleDispatchItem = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!order || !serialNumber.trim()) return;
    
    setLoading(true);
    
    try {
      const response = await apiClient.post('/crm-api/products/retailer-branch/order/dispatch-item/', {
        order_number: order.order_number,
        serial_number: serialNumber,
        order_item_id: selectedOrderItem?.id,
        notes: notes
      });
      
      const data: DispatchResult = response.data;
      
      // Update dispatched items list
      if (data.item) {
        setDispatchedItems(prev => [...prev, data.item!]);
      }
      
      // Refresh order to get updated fulfillment status
      const orderResponse = await apiClient.get(`/crm-api/products/retailer-branch/order/verify/${encodeURIComponent(order.order_number)}/`);
      setOrder(orderResponse.data);
      
      setResult({ success: true, message: data.message });
      setSerialNumber('');
      setNotes('');
      setSelectedOrderItem(null);
      
      // Check if all items dispatched
      if (data.order_fulfillment?.all_dispatched) {
        setResult({
          success: true,
          message: `🎉 All items for order ${order.order_number} have been dispatched!`
        });
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } }; message?: string };
      setResult({
        success: false,
        message: error.response?.data?.error || error.message || 'Failed to dispatch item.'
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle barcode scan
  const handleScan = (barcode: string) => {
    setShowScanner(false);
    if (scanMode === 'order') {
      setOrderNumber(barcode);
      // Auto-verify if we have an order number
      setTimeout(() => {
        handleVerifyOrder();
      }, 100);
    } else {
      setSerialNumber(barcode);
    }
  };

  // Calculate progress
  const calculateProgress = () => {
    if (!order) return { total: 0, assigned: 0, percentage: 0 };
    const total = order.items.reduce((sum, item) => sum + item.quantity, 0);
    const assigned = order.items.reduce((sum, item) => sum + item.units_assigned, 0);
    return {
      total,
      assigned,
      percentage: total > 0 ? Math.round((assigned / total) * 100) : 0
    };
  };

  const progress = calculateProgress();

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 flex items-center">
          <FiTruck className="mr-3 text-indigo-600" />
          Order-Based Dispatch
        </h1>
        <p className="text-gray-600 mt-2">
          Verify an order and scan items to dispatch. Each item&apos;s barcode/serial number is recorded.
        </p>
      </div>

      {/* Result Message */}
      {result && (
        <div className={`mb-6 p-4 rounded-lg flex items-center ${
          result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          {result.success ? (
            <FiCheck className="text-green-600 mr-3 h-5 w-5 flex-shrink-0" />
          ) : (
            <FiAlertCircle className="text-red-600 mr-3 h-5 w-5 flex-shrink-0" />
          )}
          <span className={result.success ? 'text-green-800' : 'text-red-800'}>
            {result.message}
          </span>
        </div>
      )}

      {/* Step 1: Order Verification */}
      <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-800 flex items-center mb-4">
          <FiSearch className="mr-2 text-indigo-600" />
          Step 1: Verify Order
        </h2>
        <form onSubmit={handleVerifyOrder} className="flex gap-3">
          <input
            type="text"
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Enter order/invoice number"
          />
          <button
            type="button"
            onClick={() => { setScanMode('order'); setShowScanner(true); }}
            className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            title="Scan order barcode"
          >
            <FiCamera className="h-5 w-5" />
          </button>
          <button
            type="submit"
            disabled={loading || !orderNumber.trim()}
            className="px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Verifying...' : 'Verify'}
          </button>
        </form>
      </div>

      {/* Order Details & Items */}
      {order && (
        <>
          {/* Order Summary */}
          <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Order: {order.order_number}
                </h3>
                {order.customer_name && (
                  <p className="text-gray-600">Customer: {order.customer_name}</p>
                )}
              </div>
              <div className="text-right">
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                  order.is_eligible_for_dispatch
                    ? 'bg-green-100 text-green-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {order.is_eligible_for_dispatch ? 'Ready for Dispatch' : 'Not Ready'}
                </span>
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Dispatch Progress</span>
                <span>{progress.assigned} / {progress.total} items ({progress.percentage}%)</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div
                  className={`h-3 rounded-full transition-all ${
                    progress.percentage === 100 ? 'bg-green-500' : 'bg-indigo-600'
                  }`}
                  style={{ width: `${progress.percentage}%` }}
                />
              </div>
            </div>

            {/* Order Items Table */}
            <h4 className="font-medium text-gray-700 mb-3">Items to Dispatch:</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b bg-gray-50">
                    <th className="p-3 text-sm font-semibold text-gray-600">Product</th>
                    <th className="p-3 text-sm font-semibold text-gray-600">SKU</th>
                    <th className="p-3 text-sm font-semibold text-gray-600 text-center">Qty</th>
                    <th className="p-3 text-sm font-semibold text-gray-600 text-center">Dispatched</th>
                    <th className="p-3 text-sm font-semibold text-gray-600 text-center">Remaining</th>
                    <th className="p-3 text-sm font-semibold text-gray-600 text-center">Status</th>
                    <th className="p-3 text-sm font-semibold text-gray-600">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {order.items.map((item) => (
                    <tr key={item.id} className="border-b hover:bg-gray-50">
                      <td className="p-3">{item.product_name}</td>
                      <td className="p-3 font-mono text-sm text-gray-600">{item.product_sku}</td>
                      <td className="p-3 text-center">{item.quantity}</td>
                      <td className="p-3 text-center font-semibold text-indigo-600">{item.units_assigned}</td>
                      <td className="p-3 text-center">{item.remaining}</td>
                      <td className="p-3 text-center">
                        {item.is_fully_assigned ? (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                            <FiCheck className="mr-1" /> Complete
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                            Pending
                          </span>
                        )}
                      </td>
                      <td className="p-3">
                        {!item.is_fully_assigned && order.is_eligible_for_dispatch && (
                          <button
                            onClick={() => setSelectedOrderItem(item)}
                            className={`text-sm px-3 py-1 rounded transition-colors ${
                              selectedOrderItem?.id === item.id
                                ? 'bg-indigo-600 text-white'
                                : 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200'
                            }`}
                          >
                            {selectedOrderItem?.id === item.id ? 'Selected' : 'Select'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Step 2: Scan Items */}
          {order.is_eligible_for_dispatch && !order.items.every(i => i.is_fully_assigned) && (
            <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center mb-4">
                <FiPackage className="mr-2 text-indigo-600" />
                Step 2: Scan Item to Dispatch
              </h2>
              
              {selectedOrderItem && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 mb-4">
                  <p className="text-sm text-indigo-800">
                    <strong>Dispatching for:</strong> {selectedOrderItem.product_name} 
                    ({selectedOrderItem.remaining} remaining)
                  </p>
                </div>
              )}
              
              <form onSubmit={handleDispatchItem} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Serial Number / Barcode *
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={serialNumber}
                      onChange={(e) => setSerialNumber(e.target.value)}
                      className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      placeholder="Scan or enter item serial number"
                    />
                    <button
                      type="button"
                      onClick={() => { setScanMode('item'); setShowScanner(true); }}
                      className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <FiCamera className="h-5 w-5" />
                    </button>
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
                  <input
                    type="text"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="e.g., Packed in box 1"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !serialNumber.trim()}
                  className="w-full py-3 px-4 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors disabled:opacity-50"
                >
                  {loading ? 'Dispatching...' : 'Dispatch Item'}
                </button>
              </form>
            </div>
          )}

          {/* Dispatched Items This Session */}
          {dispatchedItems.length > 0 && (
            <div className="bg-white rounded-lg shadow-md border p-6">
              <h2 className="text-xl font-semibold text-gray-800 flex items-center mb-4">
                <FiClipboard className="mr-2 text-green-600" />
                Dispatched This Session ({dispatchedItems.length} items)
              </h2>
              <div className="space-y-2">
                {dispatchedItems.map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg"
                  >
                    <div>
                      <span className="font-medium text-gray-900">{item?.product_name}</span>
                      <span className="ml-2 text-sm text-gray-600">
                        SN: {item?.serial_number}
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      {new Date(item?.dispatch_timestamp || '').toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* Barcode Scanner Modal */}
      {showScanner && (
        <BarcodeScanner
          onScan={handleScan}
          onClose={() => setShowScanner(false)}
        />
      )}
    </main>
  );
}
