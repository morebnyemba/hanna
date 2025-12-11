'use client';

import { useState } from 'react';
import BarcodeScanner from '@/app/components/BarcodeScanner';
import apiClient from '@/app/lib/apiClient';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { AlertCircle, CheckCircle, Truck, Package, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { extractErrorMessage } from '@/app/lib/apiUtils';

interface CheckoutForm {
  serial_number: string;
  customer_name: string;
  customer_phone: string;
  notes: string;
}

interface CheckinForm {
  serial_number: string;
  notes: string;
}

export default function RetailerBranchCheckInOut() {
  const [scannerOpen, setScannerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'checkout' | 'checkin'>('checkout');
  
  // Checkout form
  const [checkoutForm, setCheckoutForm] = useState<CheckoutForm>({
    serial_number: '',
    customer_name: '',
    customer_phone: '',
    notes: '',
  });
  
  // Check-in form
  const [checkinForm, setCheckinForm] = useState<CheckinForm>({
    serial_number: '',
    notes: '',
  });

  const handleScan = (code: string) => {
    setScannerOpen(false);
    if (activeTab === 'checkout') {
      setCheckoutForm({ ...checkoutForm, serial_number: code });
    } else {
      setCheckinForm({ ...checkinForm, serial_number: code });
    }
  };

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);
    
    try {
      const response = await apiClient.post('/crm-api/products/retailer-branch/checkout/', checkoutForm);
      setMessage(response.data.message || '✓ Item checked out successfully!');
      setCheckoutForm({ 
        serial_number: '', 
        customer_name: '', 
        customer_phone: '', 
        notes: '' 
      });
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to checkout item'));
    } finally {
      setLoading(false);
    }
  };

  const handleCheckin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);
    
    try {
      const response = await apiClient.post('/crm-api/products/retailer-branch/checkin/', checkinForm);
      setMessage(response.data.message || '✓ Item checked in successfully!');
      setCheckinForm({ serial_number: '', notes: '' });
    } catch (err: unknown) {
      setError(extractErrorMessage(err, 'Failed to check-in item'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Truck className="w-6 h-6" /> 
          Retailer Branch - Check-In / Check-Out
        </h1>
      </div>

      {scannerOpen && (
        <BarcodeScanner
          isOpen={scannerOpen}
          onClose={() => setScannerOpen(false)}
          onScanSuccess={handleScan}
          scanType='serialized_item'
        />
      )}

      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as 'checkout' | 'checkin')} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="checkout" className="flex items-center gap-2">
            <ArrowUpCircle className="w-4 h-4" />
            Checkout
          </TabsTrigger>
          <TabsTrigger value="checkin" className="flex items-center gap-2">
            <ArrowDownCircle className="w-4 h-4" />
            Check-in
          </TabsTrigger>
        </TabsList>

        <TabsContent value="checkout" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ArrowUpCircle className="w-5 h-5 text-emerald-600" />
                Checkout Item to Customer
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-6">
                Send an item to a customer. The item will be marked as sold.
              </p>

              <form onSubmit={handleCheckout} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Serial Number / Barcode *
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      required
                      value={checkoutForm.serial_number}
                      onChange={(e) => setCheckoutForm({ 
                        ...checkoutForm, 
                        serial_number: e.target.value 
                      })}
                      placeholder="Enter or scan serial number"
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      onClick={() => setScannerOpen(true)}
                      variant="outline"
                      size="icon"
                    >
                      <Package className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Customer Name *
                  </label>
                  <Input
                    type="text"
                    required
                    value={checkoutForm.customer_name}
                    onChange={(e) => setCheckoutForm({ 
                      ...checkoutForm, 
                      customer_name: e.target.value 
                    })}
                    placeholder="Enter customer name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Customer Phone (Optional)
                  </label>
                  <Input
                    type="tel"
                    value={checkoutForm.customer_phone}
                    onChange={(e) => setCheckoutForm({ 
                      ...checkoutForm, 
                      customer_phone: e.target.value 
                    })}
                    placeholder="+263 77 123 4567"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Notes (Optional)
                  </label>
                  <Input
                    value={checkoutForm.notes}
                    onChange={(e) => setCheckoutForm({ 
                      ...checkoutForm, 
                      notes: e.target.value 
                    })}
                    placeholder="Add any relevant notes..."
                  />
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full"
                  size="lg"
                >
                  {loading ? 'Processing...' : 'Checkout Item'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="checkin" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ArrowDownCircle className="w-5 h-5 text-blue-600" />
                Check-in Item
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-6">
                Receive an item from warehouse or as a return.
              </p>

              <form onSubmit={handleCheckin} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Serial Number / Barcode *
                  </label>
                  <div className="flex gap-2">
                    <Input
                      type="text"
                      required
                      value={checkinForm.serial_number}
                      onChange={(e) => setCheckinForm({ 
                        ...checkinForm, 
                        serial_number: e.target.value 
                      })}
                      placeholder="Enter or scan serial number"
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      onClick={() => setScannerOpen(true)}
                      variant="outline"
                      size="icon"
                    >
                      <Package className="h-4 w-4" />
                    </Button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">
                    Notes (Optional)
                  </label>
                  <Input
                    value={checkinForm.notes}
                    onChange={(e) => setCheckinForm({ 
                      ...checkinForm, 
                      notes: e.target.value 
                    })}
                    placeholder="e.g., Received from warehouse, condition notes"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full"
                  size="lg"
                >
                  {loading ? 'Processing...' : 'Check-in Item'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

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
    </div>
  );
}
