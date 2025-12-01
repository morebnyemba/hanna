// src/pages/RetailerPortalPage.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { 
  Package, 
  Box, 
  ArrowDownCircle, 
  ArrowUpCircle, 
  Plus,
  History,
  BarChart3,
  Search,
  RefreshCw
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import BarcodeScanner from '../components/BarcodeScanner';
import {
  getRetailerDashboard,
  getRetailerInventory,
  checkoutItem,
  checkinItem,
  addSerialNumber,
  scanItem,
  getTransactionHistory,
} from '../services/retailer';

const RetailerPortalPage = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [dashboard, setDashboard] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [scanMode, setScanMode] = useState(null); // 'checkout', 'checkin', 'lookup'
  const [scanResult, setScanResult] = useState(null);
  
  // Form states
  const [checkoutForm, setCheckoutForm] = useState({
    serial_number: '',
    customer_name: '',
    customer_phone: '',
    notes: ''
  });
  const [checkinForm, setCheckinForm] = useState({
    serial_number: '',
    notes: ''
  });
  const [addSerialForm, setAddSerialForm] = useState({
    product_id: '',
    serial_number: '',
    barcode: ''
  });

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getRetailerDashboard();
      setDashboard(data);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load inventory
  const loadInventory = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getRetailerInventory();
      setInventory(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load inventory:', error);
      setInventory([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load history
  const loadHistory = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getTransactionHistory();
      setHistory(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error('Failed to load history:', error);
      setHistory([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initial load based on active tab
  useEffect(() => {
    if (activeTab === 'dashboard') {
      loadDashboard();
    } else if (activeTab === 'inventory') {
      loadInventory();
    } else if (activeTab === 'history') {
      loadHistory();
    }
  }, [activeTab, loadDashboard, loadInventory, loadHistory]);

  // Handle checkout
  const handleCheckout = async (e) => {
    e.preventDefault();
    if (!checkoutForm.serial_number || !checkoutForm.customer_name) {
      toast.error('Serial number and customer name are required');
      return;
    }

    setIsLoading(true);
    try {
      const result = await checkoutItem(checkoutForm);
      toast.success(result.message || 'Item checked out successfully');
      setCheckoutForm({ serial_number: '', customer_name: '', customer_phone: '', notes: '' });
      loadDashboard();
      loadInventory();
    } catch (error) {
      toast.error(error.message || 'Failed to checkout item');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle check-in
  const handleCheckin = async (e) => {
    e.preventDefault();
    if (!checkinForm.serial_number) {
      toast.error('Serial number is required');
      return;
    }

    setIsLoading(true);
    try {
      const result = await checkinItem(checkinForm);
      toast.success(result.message || 'Item checked in successfully');
      setCheckinForm({ serial_number: '', notes: '' });
      loadDashboard();
      loadInventory();
    } catch (error) {
      toast.error(error.message || 'Failed to check-in item');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle add serial number
  const handleAddSerial = async (e) => {
    e.preventDefault();
    if (!addSerialForm.product_id || !addSerialForm.serial_number) {
      toast.error('Product ID and serial number are required');
      return;
    }

    setIsLoading(true);
    try {
      const result = await addSerialNumber({
        ...addSerialForm,
        product_id: parseInt(addSerialForm.product_id, 10)
      });
      toast.success(result.message || 'Serial number added successfully');
      setAddSerialForm({ product_id: '', serial_number: '', barcode: '' });
      loadInventory();
    } catch (error) {
      toast.error(error.message || 'Failed to add serial number');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle barcode scan
  const handleScanSuccess = async (barcode) => {
    setIsScannerOpen(false);
    
    if (scanMode === 'checkout') {
      setCheckoutForm(prev => ({ ...prev, serial_number: barcode }));
    } else if (scanMode === 'checkin') {
      setCheckinForm(prev => ({ ...prev, serial_number: barcode }));
    } else if (scanMode === 'lookup') {
      try {
        const result = await scanItem(barcode);
        setScanResult(result);
        toast.success(result.message || 'Item found');
      } catch (error) {
        toast.error(error.message || 'Item not found');
      }
    }
    
    setScanMode(null);
  };

  const openScanner = (mode) => {
    setScanMode(mode);
    setIsScannerOpen(true);
  };

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Items</CardDescription>
            <CardTitle className="text-3xl">{dashboard?.total_items || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>In Stock</CardDescription>
            <CardTitle className="text-3xl text-green-600">{dashboard?.items_in_stock || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Sold</CardDescription>
            <CardTitle className="text-3xl text-blue-600">{dashboard?.items_sold || 0}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>In Transit</CardDescription>
            <CardTitle className="text-3xl text-yellow-600">{dashboard?.items_in_transit || 0}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button onClick={() => setActiveTab('checkout')} className="h-20 text-lg">
              <ArrowUpCircle className="mr-2 h-6 w-6" />
              Checkout Item
            </Button>
            <Button onClick={() => setActiveTab('checkin')} variant="secondary" className="h-20 text-lg">
              <ArrowDownCircle className="mr-2 h-6 w-6" />
              Check-in Item
            </Button>
            <Button onClick={() => openScanner('lookup')} variant="outline" className="h-20 text-lg">
              <Search className="mr-2 h-6 w-6" />
              Scan & Lookup
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Recent Checkouts */}
      {dashboard?.recent_checkouts?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Checkouts</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {dashboard.recent_checkouts.map((item, index) => (
                <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <div>
                    <span className="font-medium">{item.product_name}</span>
                    <span className="text-sm text-gray-500 ml-2">SN: {item.serial_number}</span>
                  </div>
                  <span className="text-sm text-gray-500">{item.status_display}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );

  const renderCheckout = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowUpCircle className="h-5 w-5" />
          Checkout Item to Customer
        </CardTitle>
        <CardDescription>
          Scan or enter the serial number of the item you are sending to a customer
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleCheckout} className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1">
              <Label htmlFor="checkout_serial">Serial Number / Barcode</Label>
              <Input
                id="checkout_serial"
                value={checkoutForm.serial_number}
                onChange={(e) => setCheckoutForm(prev => ({ ...prev, serial_number: e.target.value }))}
                placeholder="Enter or scan serial number"
              />
            </div>
            <div className="flex items-end">
              <Button type="button" variant="outline" onClick={() => openScanner('checkout')}>
                Scan
              </Button>
            </div>
          </div>
          
          <div>
            <Label htmlFor="customer_name">Customer Name *</Label>
            <Input
              id="customer_name"
              value={checkoutForm.customer_name}
              onChange={(e) => setCheckoutForm(prev => ({ ...prev, customer_name: e.target.value }))}
              placeholder="Enter customer name"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="customer_phone">Customer Phone</Label>
            <Input
              id="customer_phone"
              value={checkoutForm.customer_phone}
              onChange={(e) => setCheckoutForm(prev => ({ ...prev, customer_phone: e.target.value }))}
              placeholder="Enter customer phone number"
            />
          </div>
          
          <div>
            <Label htmlFor="checkout_notes">Notes</Label>
            <Input
              id="checkout_notes"
              value={checkoutForm.notes}
              onChange={(e) => setCheckoutForm(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Optional notes"
            />
          </div>
          
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'Processing...' : 'Checkout Item'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );

  const renderCheckin = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ArrowDownCircle className="h-5 w-5" />
          Check-in Item
        </CardTitle>
        <CardDescription>
          Scan or enter the serial number of the item you are receiving
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleCheckin} className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1">
              <Label htmlFor="checkin_serial">Serial Number / Barcode</Label>
              <Input
                id="checkin_serial"
                value={checkinForm.serial_number}
                onChange={(e) => setCheckinForm(prev => ({ ...prev, serial_number: e.target.value }))}
                placeholder="Enter or scan serial number"
              />
            </div>
            <div className="flex items-end">
              <Button type="button" variant="outline" onClick={() => openScanner('checkin')}>
                Scan
              </Button>
            </div>
          </div>
          
          <div>
            <Label htmlFor="checkin_notes">Notes</Label>
            <Input
              id="checkin_notes"
              value={checkinForm.notes}
              onChange={(e) => setCheckinForm(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Optional notes (e.g., source, condition)"
            />
          </div>
          
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'Processing...' : 'Check-in Item'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );

  const renderInventory = () => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            My Inventory
          </CardTitle>
          <CardDescription>
            Items currently in your retail location
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={loadInventory}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {inventory.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <Box className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No items in inventory</p>
          </div>
        ) : (
          <div className="space-y-2">
            {inventory.map((item, index) => (
              <div key={index} className="flex justify-between items-center p-3 border rounded-lg hover:bg-gray-50">
                <div>
                  <div className="font-medium">{item.product_name}</div>
                  <div className="text-sm text-gray-500">
                    SN: {item.serial_number}
                    {item.barcode && ` | Barcode: ${item.barcode}`}
                  </div>
                </div>
                <div className="text-right">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    item.status === 'in_stock' ? 'bg-green-100 text-green-800' :
                    item.status === 'sold' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {item.status_display || item.status?.replace(/_/g, ' ')}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderAddSerial = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Plus className="h-5 w-5" />
          Add Serial Number
        </CardTitle>
        <CardDescription>
          Register a new serialized item for a product
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleAddSerial} className="space-y-4">
          <div>
            <Label htmlFor="product_id">Product ID *</Label>
            <Input
              id="product_id"
              type="number"
              value={addSerialForm.product_id}
              onChange={(e) => setAddSerialForm(prev => ({ ...prev, product_id: e.target.value }))}
              placeholder="Enter product ID"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="new_serial">Serial Number *</Label>
            <Input
              id="new_serial"
              value={addSerialForm.serial_number}
              onChange={(e) => setAddSerialForm(prev => ({ ...prev, serial_number: e.target.value }))}
              placeholder="Enter serial number"
              required
            />
          </div>
          
          <div>
            <Label htmlFor="new_barcode">Barcode (Optional)</Label>
            <Input
              id="new_barcode"
              value={addSerialForm.barcode}
              onChange={(e) => setAddSerialForm(prev => ({ ...prev, barcode: e.target.value }))}
              placeholder="Enter barcode"
            />
          </div>
          
          <Button type="submit" disabled={isLoading} className="w-full">
            {isLoading ? 'Adding...' : 'Add Serial Number'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );

  const renderHistory = () => (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            <History className="h-5 w-5" />
            Transaction History
          </CardTitle>
          <CardDescription>
            Recent check-ins and checkouts
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={loadHistory}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </CardHeader>
      <CardContent>
        {history.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <History className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>No transaction history</p>
          </div>
        ) : (
          <div className="space-y-2">
            {history.map((item, index) => (
              <div key={index} className="p-3 border rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-medium">
                      {item.from_location_display || item.from_location} → {item.to_location_display || item.to_location}
                    </div>
                    <div className="text-sm text-gray-500">
                      {item.transfer_reason_display || item.transfer_reason}
                    </div>
                    {item.notes && (
                      <div className="text-sm text-gray-400 mt-1">{item.notes}</div>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(item.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );

  // Scan result modal
  const renderScanResult = () => {
    if (!scanResult) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={() => setScanResult(null)}>
        <Card className="max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
          <CardHeader>
            <CardTitle>Scan Result</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <p className={`text-lg font-medium ${scanResult.found ? 'text-green-600' : 'text-red-600'}`}>
                {scanResult.found ? 'Item Found' : 'Item Not Found'}
              </p>
              <p className="text-gray-600">{scanResult.message}</p>
              
              {scanResult.found && scanResult.data && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  {scanResult.type === 'product' ? (
                    <>
                      <p><strong>Product:</strong> {scanResult.data.name}</p>
                      <p><strong>SKU:</strong> {scanResult.data.sku || 'N/A'}</p>
                      <p><strong>Price:</strong> {scanResult.data.price ? `${scanResult.data.currency} ${scanResult.data.price}` : 'N/A'}</p>
                    </>
                  ) : (
                    <>
                      <p><strong>Product:</strong> {scanResult.data.product_details?.name || scanResult.data.product?.name}</p>
                      <p><strong>Serial:</strong> {scanResult.data.serial_number}</p>
                      <p><strong>Status:</strong> {scanResult.data.status_display || scanResult.data.status}</p>
                      <p><strong>Location:</strong> {scanResult.data.current_location_display || scanResult.data.current_location}</p>
                      {scanResult.is_in_inventory !== undefined && (
                        <p className={`mt-2 font-medium ${scanResult.is_in_inventory ? 'text-green-600' : 'text-yellow-600'}`}>
                          {scanResult.is_in_inventory ? '✓ In your inventory' : '⚠ Not in your inventory'}
                        </p>
                      )}
                    </>
                  )}
                </div>
              )}
            </div>
            <Button className="w-full mt-4" onClick={() => setScanResult(null)}>
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4 max-w-6xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Retailer Portal</h1>
        <p className="text-gray-600">
          Manage your inventory, check-in and checkout products
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        <Button
          variant={activeTab === 'dashboard' ? 'default' : 'outline'}
          onClick={() => setActiveTab('dashboard')}
        >
          <BarChart3 className="mr-2 h-4 w-4" />
          Dashboard
        </Button>
        <Button
          variant={activeTab === 'checkout' ? 'default' : 'outline'}
          onClick={() => setActiveTab('checkout')}
        >
          <ArrowUpCircle className="mr-2 h-4 w-4" />
          Checkout
        </Button>
        <Button
          variant={activeTab === 'checkin' ? 'default' : 'outline'}
          onClick={() => setActiveTab('checkin')}
        >
          <ArrowDownCircle className="mr-2 h-4 w-4" />
          Check-in
        </Button>
        <Button
          variant={activeTab === 'inventory' ? 'default' : 'outline'}
          onClick={() => setActiveTab('inventory')}
        >
          <Package className="mr-2 h-4 w-4" />
          Inventory
        </Button>
        <Button
          variant={activeTab === 'addSerial' ? 'default' : 'outline'}
          onClick={() => setActiveTab('addSerial')}
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Serial
        </Button>
        <Button
          variant={activeTab === 'history' ? 'default' : 'outline'}
          onClick={() => setActiveTab('history')}
        >
          <History className="mr-2 h-4 w-4" />
          History
        </Button>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {isLoading && activeTab === 'dashboard' && !dashboard && (
          <div className="text-center py-8">Loading...</div>
        )}
        
        {activeTab === 'dashboard' && dashboard && renderDashboard()}
        {activeTab === 'checkout' && renderCheckout()}
        {activeTab === 'checkin' && renderCheckin()}
        {activeTab === 'inventory' && renderInventory()}
        {activeTab === 'addSerial' && renderAddSerial()}
        {activeTab === 'history' && renderHistory()}
      </div>

      {/* Barcode Scanner Modal */}
      <BarcodeScanner
        isOpen={isScannerOpen}
        onClose={() => {
          setIsScannerOpen(false);
          setScanMode(null);
        }}
        onScanSuccess={handleScanSuccess}
        onScanError={(err) => console.log('Scan error:', err)}
        scanType="serialized_item"
      />

      {/* Scan Result Modal */}
      {renderScanResult()}
    </div>
  );
};

export default RetailerPortalPage;
