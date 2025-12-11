'use client';

import { useEffect, useState } from 'react';
import BarcodeScanner from '@/app/components/BarcodeScanner';
import apiClient from '@/app/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AlertCircle, CheckCircle, Truck, Package, History, TrendingUp } from 'lucide-react';

const LOCATIONS = [
  { value: 'warehouse', label: 'Warehouse' },
  { value: 'customer', label: 'Customer' },
  { value: 'technician', label: 'Technician' },
  { value: 'manufacturer', label: 'Manufacturer' },
  { value: 'retail', label: 'Retail' },
  { value: 'outsourced', label: 'Outsourced' },
  { value: 'disposed', label: 'Disposed' }
];

interface ItemData {
  id: string;
  serial_number: string;
  barcode: string;
  status: string;
  current_location: string;
  product: { 
    name: string;
    sku?: string;
    id?: string;
  };
}

interface OrderItem {
  id: number;
  product_name: string;
  product_sku: string;
  quantity: number;
  units_assigned: number;
  is_fully_assigned: boolean;
  fulfillment_percentage: number;
}

interface OrderSummary {
  id: string;
  order_number: string;
  items: OrderItem[];
}

interface ItemHistory {
  id: number;
  timestamp: string;
  from_location: string;
  to_location: string;
  reason: string;
  notes: string;
  transferred_by: { username: string };
}

interface CheckInOutManagerProps {
  defaultLocation?: string;
  showOrderFulfillment?: boolean;
  title?: string;
}

export default function CheckInOutManager({ 
  defaultLocation = 'warehouse',
  showOrderFulfillment = true,
  title = 'Item Check-In / Check-Out'
}: CheckInOutManagerProps) {
  const [scannerOpen, setScannerOpen] = useState(false);
  const [item, setItem] = useState<ItemData | null>(null);
  const [destination, setDestination] = useState(defaultLocation);
  const [arrivalLocation, setArrivalLocation] = useState(defaultLocation);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Order fulfillment state
  const [pendingOrders, setPendingOrders] = useState<OrderSummary[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string>('');
  const [selectedOrderItemId, setSelectedOrderItemId] = useState<number | null>(null);
  const [fulfillmentError, setFulfillmentError] = useState<string | null>(null);
  const [fulfillmentMessage, setFulfillmentMessage] = useState<string | null>(null);

  // Item history state
  const [itemHistory, setItemHistory] = useState<ItemHistory[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const selectedOrder = pendingOrders.find(o => o.id === selectedOrderId);

  const loadPendingOrders = async () => {
    setOrdersLoading(true); 
    setFulfillmentError(null);
    try {
      const res = await apiClient.get('/crm-api/orders/pending-fulfillment/');
      setPendingOrders(res.data);
    } catch (e: unknown) {
      const error = e as { response?: { data?: { error?: string } } };
      setFulfillmentError(error.response?.data?.error || 'Failed to load pending orders');
    } finally { 
      setOrdersLoading(false); 
    }
  };

  const loadItemHistory = async (itemId: string) => {
    setHistoryLoading(true);
    try {
      const res = await apiClient.get(`/crm-api/items/${itemId}/location-history/`);
      setItemHistory(res.data);
      setShowHistory(true);
    } catch (e: unknown) {
      console.error('Failed to load item history:', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    // Clear selection when destination changes away from customer
    if (destination !== 'customer') {
      setSelectedOrderId('');
      setSelectedOrderItemId(null);
    }
  }, [destination]);

  const handleScan = async (code: string) => {
    setMessage(null); 
    setError(null); 
    setItem(null);
    setShowHistory(false);
    setItemHistory([]);
    
    try {
      const res = await apiClient.post('/crm-api/products/barcode/scan/', { 
        barcode: code, 
        scan_type: 'serialized_item' 
      });
      
      if (res.data.found && res.data.item_type === 'serialized_item') {
        setItem(res.data.data);
      } else {
        setError('Serialized item not found');
      }
    } catch (e: unknown) {
      const error = e as { response?: { data?: { message?: string } } };
      setError(error.response?.data?.message || 'Lookup failed');
    }
  };

  const checkout = async () => {
    if (!item) return;
    
    setLoading(true); 
    setMessage(null); 
    setError(null);
    setFulfillmentMessage(null);
    
    try {
      const body: Record<string, string | number> = { 
        destination_location: destination, 
        notes 
      };
      
      if (destination === 'customer' && selectedOrderItemId) {
        body.order_item_id = selectedOrderItemId;
      }
      
      const res = await apiClient.post(`/crm-api/items/${item.id}/checkout/`, body);
      
      if (res.data.fulfillment) {
        setFulfillmentMessage(
          `✓ Assigned ${res.data.fulfillment.units_assigned}/${res.data.fulfillment.quantity_ordered} units for Order ${res.data.fulfillment.order_number}`
        );
      }
      
      setMessage('✓ Item checked out and marked in transit successfully');
      
      // Refresh item state
      setItem({ 
        ...item, 
        status: 'in_transit', 
        current_location: 'in_transit' 
      });
      
      // Clear form
      setNotes('');
      setSelectedOrderId('');
      setSelectedOrderItemId(null);
      
    } catch (e: unknown) {
      const error = e as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Checkout failed');
    } finally { 
      setLoading(false); 
    }
  };

  const checkin = async () => {
    if (!item) return;
    
    setLoading(true); 
    setMessage(null); 
    setError(null);
    
    try {
      const res = await apiClient.post(`/crm-api/items/${item.id}/checkin/`, { 
        new_location: arrivalLocation, 
        notes 
      });
      
      setMessage('✓ Item checked in successfully');
      
      setItem({ 
        ...item, 
        status: res.data.serialized_item?.status || 'in_stock', 
        current_location: arrivalLocation 
      });
      
      // Clear form
      setNotes('');
      
    } catch (e: unknown) {
      const error = e as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Check-in failed');
    } finally { 
      setLoading(false); 
    }
  };

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      'in_stock': 'bg-green-100 text-green-800 border-green-200',
      'in_transit': 'bg-blue-100 text-blue-800 border-blue-200',
      'sold': 'bg-purple-100 text-purple-800 border-purple-200',
      'defective': 'bg-red-100 text-red-800 border-red-200',
      'returned': 'bg-yellow-100 text-yellow-800 border-yellow-200',
    };
    return colors[status] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getLocationBadgeColor = (location: string) => {
    const colors: Record<string, string> = {
      'warehouse': 'bg-blue-100 text-blue-800',
      'customer': 'bg-purple-100 text-purple-800',
      'technician': 'bg-orange-100 text-orange-800',
      'manufacturer': 'bg-indigo-100 text-indigo-800',
      'retail': 'bg-green-100 text-green-800',
      'in_transit': 'bg-yellow-100 text-yellow-800',
    };
    return colors[location] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Truck className="w-6 h-6" /> 
          {title}
        </h1>
        <Button onClick={() => setScannerOpen(true)} size="lg">
          <Package className="w-4 h-4 mr-2" />
          Scan Barcode
        </Button>
      </div>

      {scannerOpen && (
        <BarcodeScanner
          isOpen={scannerOpen}
          onClose={() => setScannerOpen(false)}
          onScanSuccess={(code) => { 
            setScannerOpen(false); 
            handleScan(code); 
          }}
          scanType='serialized_item'
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Scanned Item</span>
            {item && (
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => loadItemHistory(item.id)}
                disabled={historyLoading}
              >
                <History className="w-4 h-4 mr-2" />
                {historyLoading ? 'Loading...' : 'View History'}
              </Button>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {!item && (
            <div className="text-center py-8">
              <Package className="w-12 h-12 mx-auto mb-3 text-gray-400" />
              <p className="text-sm text-gray-500">Scan a serialized item barcode to begin.</p>
            </div>
          )}
          
          {item && (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-gray-500 mb-1">Product</p>
                  <p className="text-sm font-medium">{item.product.name}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Serial Number</p>
                  <p className="text-sm font-mono">{item.serial_number}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Barcode</p>
                  <p className="text-sm font-mono">{item.barcode}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Status</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusBadgeColor(item.status)}`}>
                    {item.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-gray-500 mb-1">Current Location</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getLocationBadgeColor(item.current_location)}`}>
                    {item.current_location.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
              </div>

              {showHistory && itemHistory.length > 0 && (
                <div className="mt-4 border-t pt-4">
                  <h4 className="text-sm font-medium mb-3 flex items-center">
                    <TrendingUp className="w-4 h-4 mr-2" />
                    Movement History
                  </h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {itemHistory.map((hist) => (
                      <div key={hist.id} className="text-xs p-2 bg-gray-50 rounded border">
                        <div className="flex justify-between mb-1">
                          <span className="font-medium">
                            {hist.from_location} → {hist.to_location}
                          </span>
                          <span className="text-gray-500">
                            {new Date(hist.timestamp).toLocaleDateString()}
                          </span>
                        </div>
                        {hist.notes && <p className="text-gray-600">{hist.notes}</p>}
                        <p className="text-gray-500">By: {hist.transferred_by?.username || 'System'}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {item && item.current_location !== 'in_transit' && (
        <Card>
          <CardHeader>
            <CardTitle>Checkout Item</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Destination Location</label>
              <select 
                value={destination} 
                onChange={e => setDestination(e.target.value)} 
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {LOCATIONS.map(loc => (
                  <option key={loc.value} value={loc.value}>
                    {loc.label}
                  </option>
                ))}
              </select>
            </div>

            {showOrderFulfillment && destination === 'customer' && (
              <div className="space-y-4 border rounded-lg p-4 bg-blue-50/30">
                <h4 className="font-medium text-sm flex items-center">
                  <Package className="w-4 h-4 mr-2" />
                  Order Fulfillment (Optional)
                </h4>
                
                {!pendingOrders.length && (
                  <Button 
                    variant="outline" 
                    size="sm" 
                    disabled={ordersLoading} 
                    onClick={loadPendingOrders}
                  >
                    {ordersLoading ? 'Loading Orders...' : 'Load Pending Orders'}
                  </Button>
                )}
                
                {pendingOrders.length > 0 && (
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-medium mb-1 block">Select Order</label>
                      <select
                        className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                        value={selectedOrderId}
                        onChange={e => { 
                          setSelectedOrderId(e.target.value); 
                          setSelectedOrderItemId(null); 
                        }}
                      >
                        <option value="">-- Choose order --</option>
                        {pendingOrders.map(o => (
                          <option key={o.id} value={o.id}>
                            {o.order_number || o.id}
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    {selectedOrderId && (
                      <div className="space-y-2">
                        <label className="text-xs font-medium mb-1 block">Select Matching Order Line</label>
                        <select
                          className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500"
                          value={selectedOrderItemId ?? ''}
                          onChange={e => setSelectedOrderItemId(Number(e.target.value))}
                        >
                          <option value="">-- Choose line item --</option>
                          {selectedOrder?.items.map(line => (
                            <option
                              key={line.id}
                              value={line.id}
                              disabled={line.is_fully_assigned}
                            >
                              {line.product_name} • {line.units_assigned}/{line.quantity} assigned
                              {line.is_fully_assigned ? ' (Full)' : ''}
                            </option>
                          ))}
                        </select>
                        
                        {selectedOrderItemId && (
                          <p className="text-xs text-blue-600 bg-blue-50 p-2 rounded">
                            ℹ This physical unit will be linked to the selected order line on checkout.
                          </p>
                        )}
                      </div>
                    )}
                    
                    {fulfillmentError && (
                      <p className="text-xs text-red-600 bg-red-50 p-2 rounded">{fulfillmentError}</p>
                    )}
                  </div>
                )}
              </div>
            )}

            <div>
              <label className="text-sm font-medium mb-2 block">Notes (Optional)</label>
              <Input 
                value={notes} 
                onChange={e => setNotes(e.target.value)} 
                placeholder="Add any relevant notes..." 
                className="w-full"
              />
            </div>
            
            <Button 
              disabled={loading} 
              onClick={checkout}
              className="w-full"
              size="lg"
            >
              {loading ? 'Processing...' : 'Checkout & Mark In Transit'}
            </Button>
          </CardContent>
        </Card>
      )}

      {item && item.current_location === 'in_transit' && (
        <Card>
          <CardHeader>
            <CardTitle>Check-In Item</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Arrival Location</label>
              <select 
                value={arrivalLocation} 
                onChange={e => setArrivalLocation(e.target.value)} 
                className="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                {LOCATIONS.map(loc => (
                  <option key={loc.value} value={loc.value}>
                    {loc.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">Notes (Optional)</label>
              <Input 
                value={notes} 
                onChange={e => setNotes(e.target.value)} 
                placeholder="Add any relevant notes..." 
                className="w-full"
              />
            </div>
            
            <Button 
              disabled={loading} 
              onClick={checkin}
              className="w-full"
              size="lg"
            >
              {loading ? 'Processing...' : 'Complete Check-In'}
            </Button>
          </CardContent>
        </Card>
      )}

      {(message || error || fulfillmentMessage) && (
        <div className="space-y-2">
          {(message || error) && (
            <div className={`p-4 rounded-lg text-sm flex items-center gap-3 ${
              error 
                ? 'bg-red-50 text-red-700 border border-red-200' 
                : 'bg-green-50 text-green-700 border border-green-200'
            }`}>
              {error ? (
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
              ) : (
                <CheckCircle className="w-5 h-5 flex-shrink-0" />
              )}
              <span>{error || message}</span>
            </div>
          )}
          
          {fulfillmentMessage && (
            <div className="p-4 rounded-lg text-sm flex items-center gap-3 bg-blue-50 text-blue-700 border border-blue-200">
              <CheckCircle className="w-5 h-5 flex-shrink-0" />
              <span>{fulfillmentMessage}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
