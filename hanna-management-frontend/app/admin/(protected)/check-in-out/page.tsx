'use client';

import { useEffect, useState } from 'react';
import BarcodeScanner from '@/app/components/BarcodeScanner';
import apiClient from '@/app/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { AlertCircle, CheckCircle, Truck } from 'lucide-react';
import { Input } from '@/components/ui/input';

const LOCATIONS = [
  'warehouse','customer','technician','manufacturer','retail','outsourced','disposed'
];

interface ItemData {
  id: string;
  serial_number: string;
  barcode: string;
  status: string;
  current_location: string;
  product: { name: string };
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

export default function AdminCheckInOutPage() {
  const [scannerOpen, setScannerOpen] = useState(false);
  const [item, setItem] = useState<ItemData | null>(null);
  const [destination, setDestination] = useState('warehouse');
  const [arrivalLocation, setArrivalLocation] = useState('warehouse');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // --- Fulfillment state ---
  const [pendingOrders, setPendingOrders] = useState<OrderSummary[]>([]);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string>('');
  const [selectedOrderItemId, setSelectedOrderItemId] = useState<number | null>(null);
  const [fulfillmentError, setFulfillmentError] = useState<string | null>(null);
  const [fulfillmentMessage, setFulfillmentMessage] = useState<string | null>(null);

  const selectedOrder = pendingOrders.find(o => o.id === selectedOrderId);
  const matchingOrderItems = selectedOrder?.items.filter(i => i.product_name === item?.product.name || i.product_sku) || [];

  const loadPendingOrders = async () => {
    setOrdersLoading(true); setFulfillmentError(null);
    try {
      const res = await apiClient.get('/crm-api/orders/pending-fulfillment/');
      setPendingOrders(res.data);
    } catch (e:any) {
      setFulfillmentError(e.response?.data?.error || 'Failed to load pending orders');
    } finally { setOrdersLoading(false); }
  };

  useEffect(() => {
    // Clear selection when destination changes away from customer
    if (destination !== 'customer') {
      setSelectedOrderId('');
      setSelectedOrderItemId(null);
    }
  }, [destination]);

  const handleScan = async (code: string) => {
    setMessage(null); setError(null); setItem(null);
    try {
      const res = await apiClient.post('/crm-api/products/barcode/scan/', { barcode: code, scan_type: 'serialized_item' });
      if (res.data.found && res.data.item_type === 'serialized_item') {
        setItem(res.data.data);
      } else {
        setError('Serialized item not found');
      }
    } catch (e:any) {
      setError(e.response?.data?.message || 'Lookup failed');
    }
  };

  const checkout = async () => {
    if (!item) return;
    setLoading(true); setMessage(null); setError(null);
    try {
      const body: any = { destination_location: destination, notes };
      if (destination === 'customer' && selectedOrderItemId) {
        body.order_item_id = selectedOrderItemId;
      }
      const res = await apiClient.post(`/crm-api/items/${item.id}/checkout/`, body);
      if (res.data.fulfillment) {
        setFulfillmentMessage(
          `Assigned ${res.data.fulfillment.units_assigned}/${res.data.fulfillment.quantity_ordered} units for Order ${res.data.fulfillment.order_number}`
        );
      }
      setMessage('Item checked out and marked in transit');
      // Refresh item state
      setItem({ ...item, status: 'in_transit', current_location: 'in_transit' });
    } catch (e:any) {
      setError(e.response?.data?.error || 'Checkout failed');
    } finally { setLoading(false); }
  };

  const checkin = async () => {
    if (!item) return;
    setLoading(true); setMessage(null); setError(null);
    try {
      const res = await apiClient.post(`/crm-api/items/${item.id}/checkin/`, { new_location: arrivalLocation, notes });
      setMessage('Item checked in successfully');
      setItem({ ...item, status: res.data.serialized_item?.status || item.status, current_location: arrivalLocation });
    } catch (e:any) {
      setError(e.response?.data?.error || 'Check-in failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2"><Truck className="w-6 h-6" /> Item Check-In / Check-Out</h1>
        <Button onClick={() => setScannerOpen(true)}>Scan Barcode</Button>
      </div>

      {scannerOpen && (
        <BarcodeScanner
          isOpen={scannerOpen}
          onClose={() => setScannerOpen(false)}
          onScanSuccess={(code) => { setScannerOpen(false); handleScan(code); }}
          scanType='serialized_item'
        />
      )}

      <Card>
        <CardHeader>
          <CardTitle>Scanned Item</CardTitle>
        </CardHeader>
        <CardContent>
          {!item && <p className="text-sm text-gray-500">Scan a serialized item barcode to begin.</p>}
          {item && (
            <div className="space-y-3">
              <p className="text-sm"><span className="font-medium">Product:</span> {item.product.name}</p>
              <p className="text-sm"><span className="font-medium">Serial:</span> {item.serial_number}</p>
              <p className="text-sm"><span className="font-medium">Barcode:</span> {item.barcode}</p>
              <p className="text-sm"><span className="font-medium">Status:</span> {item.status}</p>
              <p className="text-sm"><span className="font-medium">Location:</span> {item.current_location}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {item && item.current_location !== 'in_transit' && (
        <Card>
          <CardHeader><CardTitle>Checkout Item</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Destination Location</label>
              <select value={destination} onChange={e=>setDestination(e.target.value)} className="mt-1 w-full border rounded px-2 py-2 text-sm">
                {LOCATIONS.map(loc => <option key={loc} value={loc}>{loc}</option>)}
              </select>
            </div>
            {destination === 'customer' && (
              <div className="space-y-4 border rounded-md p-4 bg-muted/30">
                <h4 className="font-medium text-sm">Order Fulfillment (Optional)</h4>
                {!pendingOrders.length && (
                  <Button variant="outline" size="sm" disabled={ordersLoading} onClick={loadPendingOrders}>
                    {ordersLoading ? 'Loading Orders...' : 'Load Pending Orders'}
                  </Button>
                )}
                {pendingOrders.length > 0 && (
                  <div className="space-y-3">
                    <div>
                      <label className="text-xs font-medium">Select Order</label>
                      <select
                        className="mt-1 w-full border rounded px-2 py-2 text-sm"
                        value={selectedOrderId}
                        onChange={e => { setSelectedOrderId(e.target.value); setSelectedOrderItemId(null); }}
                      >
                        <option value="">-- choose order --</option>
                        {pendingOrders.map(o => (
                          <option key={o.id} value={o.id}>{o.order_number || o.id}</option>
                        ))}
                      </select>
                    </div>
                    {selectedOrderId && (
                      <div className="space-y-2">
                        <label className="text-xs font-medium">Select Matching Order Line</label>
                        <select
                          className="mt-1 w-full border rounded px-2 py-2 text-sm"
                          value={selectedOrderItemId ?? ''}
                          onChange={e => setSelectedOrderItemId(Number(e.target.value))}
                        >
                          <option value="">-- choose line item --</option>
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
                          <p className="text-xs text-gray-600">
                            Linking this physical unit to the selected order line on checkout.
                          </p>
                        )}
                      </div>
                    )}
                    {fulfillmentError && <p className="text-xs text-red-600">{fulfillmentError}</p>}
                    {fulfillmentMessage && <p className="text-xs text-green-600">{fulfillmentMessage}</p>}
                  </div>
                )}
              </div>
            )}
            <div>
              <label className="text-sm font-medium">Notes</label>
              <Input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Optional notes" />
            </div>
            <Button disabled={loading} onClick={checkout}>Checkout & Mark In Transit</Button>
          </CardContent>
        </Card>
      )}

      {item && item.current_location === 'in_transit' && (
        <Card>
          <CardHeader><CardTitle>Check-In Item</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Arrival Location</label>
              <select value={arrivalLocation} onChange={e=>setArrivalLocation(e.target.value)} className="mt-1 w-full border rounded px-2 py-2 text-sm">
                {LOCATIONS.map(loc => <option key={loc} value={loc}>{loc}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Notes</label>
              <Input value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Optional notes" />
            </div>
            <Button disabled={loading} onClick={checkin}>Complete Check-In</Button>
          </CardContent>
        </Card>
      )}

      {(message || error) && (
        <div className={`p-4 rounded-md text-sm flex items-center gap-2 ${error? 'bg-red-50 text-red-700 border border-red-200':'bg-green-50 text-green-700 border border-green-200'}`}>
          {error? <AlertCircle className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
          {error || message}
        </div>
      )}
    </div>
  );
}
