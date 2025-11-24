'use client';

import { useState } from 'react';
import BarcodeScanner from '@/app/components/BarcodeScanner';
import apiClient from '@/app/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AlertCircle, CheckCircle, Truck } from 'lucide-react';

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

export default function ManufacturerCheckInOutPage() {
  const [scannerOpen, setScannerOpen] = useState(false);
  const [item, setItem] = useState<ItemData | null>(null);
  const [destination, setDestination] = useState('manufacturer');
  const [arrivalLocation, setArrivalLocation] = useState('manufacturer');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
      await apiClient.post(`/crm-api/items/${item.id}/checkout/`, { destination_location: destination, notes });
      setMessage('Item checked out and marked in transit');
      setItem({ ...item, status: 'in_transit', current_location: 'in_transit' });
    } catch (e:any) {
      setError(e.response?.data?.error || 'Checkout failed');
    } finally { setLoading(false); }
  };

  const checkin = async () => {
    if (!item) return;
    setLoading(true); setMessage(null); setError(null);
    try {
      await apiClient.post(`/crm-api/items/${item.id}/checkin/`, { new_location: arrivalLocation, notes });
      setMessage('Item checked in successfully');
      setItem({ ...item, status: 'in_stock', current_location: arrivalLocation });
    } catch (e:any) {
      setError(e.response?.data?.error || 'Check-in failed');
    } finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2"><Truck className="w-6 h-6" /> Manufacturer Check-In / Check-Out</h1>
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
