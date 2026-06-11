'use client';

import { useState } from 'react';
import Link from 'next/link';
import { FiArrowLeft, FiSearch, FiPackage, FiCheck, FiClock, FiAlertCircle, FiTruck } from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';

interface OrderItem {
  product_name: string;
  quantity: number;
}

interface OrderResult {
  order_number: string;
  stage: string;
  stage_display: string;
  payment_status: string;
  payment_status_display: string;
  tracking_number: string | null;
  dispatch_date: string | null;
  amount: string;
  currency: string;
  items: OrderItem[];
}

const STAGE_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string; done: boolean }> = {
  prospecting:   { label: 'Order Received',    icon: <FiCheck />,   color: 'bg-sky-500',    done: true },
  qualification: { label: 'Confirmed',         icon: <FiCheck />,   color: 'bg-sky-600',    done: true },
  proposal:      { label: 'Preparing',         icon: <FiClock />,   color: 'bg-orange-400', done: false },
  negotiation:   { label: 'Ready to Dispatch', icon: <FiPackage />, color: 'bg-orange-500', done: false },
  closed_won:    { label: 'Delivered / Won',   icon: <FiCheck />,   color: 'bg-green-500',  done: true },
  closed_lost:   { label: 'Cancelled',         icon: <FiAlertCircle />, color: 'bg-red-400', done: false },
};

const PAYMENT_BADGE: Record<string, string> = {
  pending:         'bg-orange-100 text-orange-700',
  paid:            'bg-green-100 text-green-700',
  partially_paid:  'bg-sky-100 text-sky-700',
  refunded:        'bg-purple-100 text-purple-700',
  not_applicable:  'bg-gray-100 text-gray-500',
};

export default function TrackOrderPage() {
  const [orderNumber, setOrderNumber] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OrderResult | null>(null);
  const [error, setError] = useState('');

  const search = async () => {
    if (!orderNumber.trim() || !email.trim()) { setError('Please enter both your order number and email.'); return; }
    setLoading(true); setError(''); setResult(null);
    try {
      const res = await apiClient.get(
        `/crm-api/customer-data/orders/track/?order_number=${encodeURIComponent(orderNumber.trim())}&email=${encodeURIComponent(email.trim())}`
      );
      setResult(res.data);
    } catch (err: any) {
      setError(err?.response?.status === 404
        ? 'Order not found. Please check your order number and email address.'
        : 'Failed to look up your order. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const stageConfig = result ? (STAGE_CONFIG[result.stage] || { label: result.stage_display, icon: <FiClock />, color: 'bg-sky-500', done: false }) : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-sky-50/30 to-purple-50/20">
      {/* Header */}
      <div className="bg-white border-b border-sky-100 sticky top-0 z-40 shadow-sm">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/shop" className="flex items-center gap-2 text-sky-600 hover:text-sky-800 font-semibold text-sm transition">
            <FiArrowLeft className="w-4 h-4" />
            Back to Shop
          </Link>
          <div className="flex-1 flex justify-center">
            <div className="flex items-center gap-2 text-sm font-bold text-sky-700">
              <FiTruck className="w-5 h-5" />
              Track Your Order
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto px-4 py-10">

        {/* Search card */}
        <div className="bg-white rounded-2xl border border-sky-100 shadow-sm p-6 mb-6">
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-sky-100 flex items-center justify-center">
              <FiSearch className="w-5 h-5 text-sky-600" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold text-sky-900">Track Your Order</h1>
              <p className="text-sm text-gray-500">Enter your order number and email to check the status.</p>
            </div>
          </div>

          <div className="space-y-3">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Order Number</label>
              <input
                type="text"
                value={orderNumber}
                onChange={(e) => { setOrderNumber(e.target.value); setError(''); }}
                onKeyDown={(e) => e.key === 'Enter' && search()}
                placeholder="e.g. ORD-2024-001"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 transition hover:border-sky-300"
              />
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-1.5">Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                onKeyDown={(e) => e.key === 'Enter' && search()}
                placeholder="The email you ordered with"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 transition hover:border-sky-300"
              />
            </div>
          </div>

          {error && (
            <div className="mt-3 flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 px-4 py-3 rounded-xl text-sm">
              <FiAlertCircle className="w-4 h-4 flex-shrink-0" />{error}
            </div>
          )}

          <button
            onClick={search}
            disabled={loading}
            className="mt-4 w-full py-3.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-bold text-sm transition disabled:bg-gray-300 flex items-center justify-center gap-2 shadow-sm"
          >
            {loading ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />Searching…</>
            ) : (
              <><FiSearch className="w-4 h-4" />Track Order</>
            )}
          </button>
        </div>

        {/* Result */}
        {result && stageConfig && (
          <div className="bg-white rounded-2xl border border-sky-100 shadow-sm overflow-hidden">
            {/* Status banner */}
            <div className={`${stageConfig.color} px-6 py-4 flex items-center gap-3`}>
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white">
                {stageConfig.icon}
              </div>
              <div>
                <p className="text-white/80 text-xs font-semibold uppercase tracking-wider">Order Status</p>
                <p className="text-white font-extrabold text-lg">{stageConfig.label}</p>
              </div>
              <div className="ml-auto text-right">
                <p className="text-white/80 text-xs">Order No.</p>
                <p className="text-white font-bold font-mono">{result.order_number}</p>
              </div>
            </div>

            <div className="p-6 space-y-5">
              {/* Payment + tracking */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Payment</p>
                  <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${PAYMENT_BADGE[result.payment_status] || 'bg-gray-100 text-gray-500'}`}>
                    {result.payment_status_display}
                  </span>
                </div>
                <div className="bg-gray-50 rounded-xl p-3">
                  <p className="text-xs text-gray-400 font-semibold uppercase tracking-wide mb-1">Amount</p>
                  <p className="font-extrabold text-orange-500">{result.currency} {parseFloat(result.amount).toFixed(2)}</p>
                </div>
              </div>

              {result.tracking_number && (
                <div className="bg-sky-50 border border-sky-200 rounded-xl p-3 flex items-center gap-2">
                  <FiTruck className="w-4 h-4 text-sky-600 flex-shrink-0" />
                  <div>
                    <p className="text-xs text-sky-500 font-semibold uppercase tracking-wide">Tracking Number</p>
                    <p className="font-bold text-sky-900 font-mono">{result.tracking_number}</p>
                  </div>
                </div>
              )}

              {result.dispatch_date && (
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <FiTruck className="w-4 h-4 text-gray-400" />
                  Dispatched on {new Date(result.dispatch_date).toLocaleDateString('en-ZW', { dateStyle: 'long' })}
                </div>
              )}

              {/* Items */}
              <div>
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">Order Items</p>
                <div className="space-y-2">
                  {result.items.map((item, i) => (
                    <div key={i} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0 text-sm">
                      <span className="text-gray-700 font-medium">{item.product_name}</span>
                      <span className="text-gray-400 font-semibold">×{item.quantity}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-sky-50 border border-sky-100 rounded-xl p-3 text-sm text-sky-700">
                💬 Questions about your order? <a href={`https://wa.me/${process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || ''}?text=${encodeURIComponent(`Hi, I have a question about order ${result.order_number}`)}`} target="_blank" rel="noopener noreferrer" className="font-bold underline">Chat on WhatsApp</a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
