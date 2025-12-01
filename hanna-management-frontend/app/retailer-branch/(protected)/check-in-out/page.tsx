'use client';

import { useState } from 'react';
import { FiArrowUpCircle, FiArrowDownCircle, FiCamera, FiCheck, FiAlertCircle } from 'react-icons/fi';
import apiClient from '@/lib/apiClient';
import BarcodeScanner from '@/app/components/BarcodeScanner';

export default function CheckInOutPage() {
  const [activeTab, setActiveTab] = useState<'checkout' | 'checkin'>('checkout');
  const [showScanner, setShowScanner] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);
  
  // Checkout form
  const [checkoutForm, setCheckoutForm] = useState({
    serial_number: '',
    customer_name: '',
    customer_phone: '',
    notes: '',
  });
  
  // Check-in form
  const [checkinForm, setCheckinForm] = useState({
    serial_number: '',
    notes: '',
  });

  const handleScan = (barcode: string) => {
    setShowScanner(false);
    if (activeTab === 'checkout') {
      setCheckoutForm({ ...checkoutForm, serial_number: barcode });
    } else {
      setCheckinForm({ ...checkinForm, serial_number: barcode });
    }
  };

  const handleCheckout = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const response = await apiClient.post('/crm-api/products/retailer-branch/checkout/', checkoutForm);
      setResult({ success: true, message: response.data.message || 'Item checked out successfully!' });
      setCheckoutForm({ serial_number: '', customer_name: '', customer_phone: '', notes: '' });
    } catch (err: any) {
      setResult({ 
        success: false, 
        message: err.response?.data?.error || err.message || 'Failed to checkout item.' 
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCheckin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    try {
      const response = await apiClient.post('/crm-api/products/retailer-branch/checkin/', checkinForm);
      setResult({ success: true, message: response.data.message || 'Item checked in successfully!' });
      setCheckinForm({ serial_number: '', notes: '' });
    } catch (err: any) {
      setResult({ 
        success: false, 
        message: err.response?.data?.error || err.message || 'Failed to check-in item.' 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-1 p-4 sm:p-8 overflow-y-auto">
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-6">Check-In / Checkout</h1>
      
      {/* Tabs */}
      <div className="flex gap-4 mb-6">
        <button
          onClick={() => { setActiveTab('checkout'); setResult(null); }}
          className={`flex items-center px-6 py-3 rounded-lg font-medium transition-colors ${
            activeTab === 'checkout'
              ? 'bg-emerald-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <FiArrowUpCircle className="mr-2" /> Checkout
        </button>
        <button
          onClick={() => { setActiveTab('checkin'); setResult(null); }}
          className={`flex items-center px-6 py-3 rounded-lg font-medium transition-colors ${
            activeTab === 'checkin'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          <FiArrowDownCircle className="mr-2" /> Check-in
        </button>
      </div>

      {/* Result Message */}
      {result && (
        <div className={`mb-6 p-4 rounded-lg flex items-center ${
          result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          {result.success ? (
            <FiCheck className="text-green-600 mr-3 h-5 w-5" />
          ) : (
            <FiAlertCircle className="text-red-600 mr-3 h-5 w-5" />
          )}
          <span className={result.success ? 'text-green-800' : 'text-red-800'}>
            {result.message}
          </span>
        </div>
      )}

      {/* Forms */}
      <div className="bg-white rounded-lg shadow-md border p-6">
        {activeTab === 'checkout' ? (
          <form onSubmit={handleCheckout} className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center">
              <FiArrowUpCircle className="mr-2 text-emerald-600" /> Checkout Item to Customer
            </h2>
            <p className="text-gray-600">Send an item to a customer. The item will be marked as sold.</p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Serial Number / Barcode *</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  required
                  value={checkoutForm.serial_number}
                  onChange={(e) => setCheckoutForm({ ...checkoutForm, serial_number: e.target.value })}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  placeholder="Enter or scan serial number"
                />
                <button
                  type="button"
                  onClick={() => setShowScanner(true)}
                  className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <FiCamera className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer Name *</label>
              <input
                type="text"
                required
                value={checkoutForm.customer_name}
                onChange={(e) => setCheckoutForm({ ...checkoutForm, customer_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="Enter customer name"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Customer Phone</label>
              <input
                type="tel"
                value={checkoutForm.customer_phone}
                onChange={(e) => setCheckoutForm({ ...checkoutForm, customer_phone: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                placeholder="+1234567890"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={checkoutForm.notes}
                onChange={(e) => setCheckoutForm({ ...checkoutForm, notes: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                rows={3}
                placeholder="Optional notes about this checkout"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Checkout Item'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleCheckin} className="space-y-6">
            <h2 className="text-xl font-semibold text-gray-800 flex items-center">
              <FiArrowDownCircle className="mr-2 text-blue-600" /> Check-in Item
            </h2>
            <p className="text-gray-600">Receive an item from warehouse or as a return.</p>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Serial Number / Barcode *</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  required
                  value={checkinForm.serial_number}
                  onChange={(e) => setCheckinForm({ ...checkinForm, serial_number: e.target.value })}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter or scan serial number"
                />
                <button
                  type="button"
                  onClick={() => setShowScanner(true)}
                  className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <FiCamera className="h-5 w-5" />
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea
                value={checkinForm.notes}
                onChange={(e) => setCheckinForm({ ...checkinForm, notes: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={3}
                placeholder="e.g., Received from warehouse, condition notes"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              {loading ? 'Processing...' : 'Check-in Item'}
            </button>
          </form>
        )}
      </div>

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
