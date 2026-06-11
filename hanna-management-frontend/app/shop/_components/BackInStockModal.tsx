'use client';

import { useState } from 'react';
import { FiX, FiBell, FiCheck, FiAlertCircle } from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';
import type { Product } from './ProductCard';

interface BackInStockModalProps {
  product: Product;
  csrfToken: string | null;
  onClose: () => void;
}

export default function BackInStockModal({ product, csrfToken, onClose }: BackInStockModalProps) {
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const submit = async () => {
    if (!email && !phone) { setError('Please enter your email or phone number.'); return; }
    setSubmitting(true); setError('');
    try {
      await apiClient.post(
        '/crm-api/products/notify-stock/',
        { product_id: product.id, email: email || null, phone: phone || null },
        csrfToken ? { headers: { 'X-CSRFToken': csrfToken } } : {}
      );
      setDone(true);
    } catch {
      setError('Failed to save notification. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-6 border border-sky-100" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className="w-9 h-9 rounded-full bg-sky-100 flex items-center justify-center">
              <FiBell className="w-4 h-4 text-sky-600" />
            </div>
            <h3 className="font-extrabold text-sky-900 text-base">Notify Me</h3>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full hover:bg-gray-100 text-gray-400 transition">
            <FiX className="w-4 h-4" />
          </button>
        </div>

        {done ? (
          <div className="text-center py-4">
            <div className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
              <FiCheck className="w-7 h-7 text-green-600" />
            </div>
            <p className="font-bold text-green-800 mb-1">You're on the list!</p>
            <p className="text-sm text-gray-500">We'll notify you as soon as <strong>{product.name}</strong> is back in stock.</p>
            <button onClick={onClose} className="mt-4 px-6 py-2 bg-sky-600 text-white rounded-xl font-bold text-sm hover:bg-sky-700 transition">
              Done
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-600 mb-4">
              <strong className="text-sky-900">{product.name}</strong> is currently out of stock. Leave your details and we'll notify you the moment it's available.
            </p>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); setError(''); }}
                  placeholder="your@email.com"
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 transition"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-600 mb-1">Phone / WhatsApp</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => { setPhone(e.target.value); setError(''); }}
                  placeholder="0771234567"
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400 transition"
                />
              </div>
            </div>

            {error && (
              <p className="mt-2 text-xs text-red-600 flex items-center gap-1">
                <FiAlertCircle className="w-3 h-3" />{error}
              </p>
            )}

            <button
              onClick={submit}
              disabled={submitting}
              className="mt-4 w-full py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-bold text-sm transition disabled:bg-gray-300"
            >
              {submitting ? 'Saving…' : 'Notify Me When Available'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
