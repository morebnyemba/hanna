'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import {
  FiCheck, FiAlertCircle, FiArrowLeft, FiShoppingCart,
  FiPackage, FiLock, FiChevronRight,
} from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';
import type { Cart } from '../_components/CartDrawer';

// ─── Types ────────────────────────────────────────────────────────────────────

interface DeliveryDetails {
  fullName: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  notes: string;
}

interface PaymentInfo {
  instructions?: string;
  paynow_reference?: string;
  payment_reference?: string;
  poll_url?: string;
  payment_method?: string;
  requires_otp?: boolean;
  otp_message?: string;
  authorization_code?: string;
  authorization_expires?: string;
  deeplink?: string;
  redirect_url?: string;
}

type PaymentMethod = 'ecocash' | 'omari' | 'innbucks' | 'telecash';

type Step = 'details' | 'confirm' | 'pay' | 'success';

type PaymentPollStatus = 'idle' | 'pending' | 'paid' | 'failed' | 'timeout';

const PAYMENT_POLL_INTERVAL_MS = 4000;
const PAYMENT_POLL_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes

const STEPS: { key: Step; label: string }[] = [
  { key: 'details', label: 'Delivery & Payment' },
  { key: 'confirm', label: 'Review Order' },
  { key: 'pay', label: 'Payment' },
  { key: 'success', label: 'Done' },
];

const PAYMENT_METHODS = [
  { value: 'ecocash' as PaymentMethod, label: 'EcoCash', icon: '💚', description: 'EcoCash mobile money' },
  { value: 'omari' as PaymentMethod, label: 'Omari', icon: '🔵', description: 'Omari wallet (OTP required)' },
  { value: 'innbucks' as PaymentMethod, label: 'Innbucks', icon: '🟣', description: 'Innbucks wallet' },
  { value: 'telecash' as PaymentMethod, label: 'Telecash', icon: '🟠', description: 'Telecash mobile money' },
] as const;

// ─── Sub-components ────────────────────────────────────────────────────────────

function StepIndicator({ step }: { step: Step }) {
  const idx = STEPS.findIndex((s) => s.key === step);
  return (
    <div className="flex items-center gap-2">
      {STEPS.map((s, i) => {
        const done = i < idx;
        const active = s.key === step;
        return (
          <div key={s.key} className="flex items-center">
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all ${
              done ? 'bg-orange-500 text-white' :
              active ? 'bg-purple-600 text-white shadow-md' :
              'bg-gray-100 text-gray-400'
            }`}>
              {done ? <FiCheck className="w-3 h-3" /> : <span>{i + 1}</span>}
              <span className="hidden sm:inline">{s.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <FiChevronRight className={`w-4 h-4 mx-1 ${i < idx ? 'text-orange-400' : 'text-gray-200'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null;
  return (
    <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
      <FiAlertCircle className="w-3 h-3 flex-shrink-0" />{msg}
    </p>
  );
}

function OrderSummary({ cart }: { cart: Cart | null }) {
  if (!cart || cart.items.length === 0) return null;
  const total = parseFloat(cart.total_price);
  const subtotal = cart.subtotal ? parseFloat(cart.subtotal) : total;
  const discount = cart.discount_amount ? parseFloat(cart.discount_amount) : 0;
  return (
    <div className="bg-white rounded-2xl border border-purple-100 shadow-sm p-5">
      <h3 className="font-extrabold text-purple-900 text-sm uppercase tracking-wider mb-4 flex items-center gap-2">
        <FiShoppingCart className="w-4 h-4" /> Order Summary
      </h3>
      <div className="space-y-3 mb-4">
        {cart.items.map((item) => (
          <div key={item.id} className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg overflow-hidden bg-gradient-to-br from-purple-50 to-sky-50 flex-shrink-0 flex items-center justify-center">
              {item.product.images && item.product.images.length > 0 ? (
                <img src={item.product.images[0].image} alt={item.product.name} className="w-full h-full object-cover" />
              ) : (
                <FiPackage className="w-4 h-4 text-purple-300" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-gray-800 line-clamp-1">{item.product.name}</p>
              <p className="text-xs text-gray-400">Qty: {item.quantity}</p>
            </div>
            <p className="text-sm font-bold text-orange-500 flex-shrink-0">
              {item.product.currency} {parseFloat(item.subtotal).toFixed(2)}
            </p>
          </div>
        ))}
      </div>
      {discount > 0 && (
        <div className="border-t border-purple-100 pt-3 space-y-1.5">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Subtotal</span>
            <span className="text-gray-700">USD {subtotal.toFixed(2)}</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-green-600">Discount {cart.coupon_code ? `(${cart.coupon_code})` : ''}</span>
            <span className="text-green-600">-USD {discount.toFixed(2)}</span>
          </div>
        </div>
      )}
      <div className={`${discount > 0 ? '' : 'border-t border-purple-100 pt-3'} flex items-center justify-between`}>
        <span className="text-sm font-semibold text-gray-600">Total</span>
        <span className="text-xl font-extrabold text-orange-500">USD {total.toFixed(2)}</span>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function CheckoutPage() {
  const router = useRouter();

  const [cart, setCart] = useState<Cart | null>(null);
  const [cartLoading, setCartLoading] = useState(true);
  const [step, setStep] = useState<Step>('details');
  const [submitting, setSubmitting] = useState(false);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);

  const [deliveryDetails, setDeliveryDetails] = useState<DeliveryDetails>({
    fullName: '', email: '', phone: '', address: '', city: '', notes: '',
  });
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof DeliveryDetails, string>>>({});
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('ecocash');
  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null);
  const [otpCode, setOtpCode] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [termsError, setTermsError] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentPollStatus, setPaymentPollStatus] = useState<PaymentPollStatus>('idle');
  const pollIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    apiClient.get('/crm-api/products/csrf/')
      .then((res) => { if (res.data?.token) setCsrfToken(res.data.token); })
      .catch(() => {});
    apiClient.get('/crm-api/products/cart/')
      .then((res) => { setCart(res.data); setCartLoading(false); })
      .catch(() => { setCartLoading(false); });
  }, []);

  const csrfHeaders = useCallback(() => (
    csrfToken ? { headers: { 'X-CSRFToken': csrfToken } } : {}
  ), [csrfToken]);

  const validateDelivery = (): boolean => {
    const errs: Partial<Record<keyof DeliveryDetails, string>> = {};
    if (!deliveryDetails.fullName.trim()) errs.fullName = 'Full name is required';
    if (!deliveryDetails.email.trim()) errs.email = 'Email is required';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(deliveryDetails.email)) errs.email = 'Enter a valid email address';
    if (!deliveryDetails.phone.trim()) errs.phone = 'Phone number is required';
    if (!deliveryDetails.address.trim()) errs.address = 'Delivery address is required';
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleFieldChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setDeliveryDetails((prev) => ({ ...prev, [name]: value }));
    if (fieldErrors[name as keyof DeliveryDetails]) {
      setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleProceedToConfirm = () => {
    if (!agreedToTerms) { setTermsError(true); return; }
    if (validateDelivery()) setStep('confirm');
  };

  const placeOrder = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const checkoutRes = await apiClient.post('/crm-api/products/cart/checkout/', {
        full_name: deliveryDetails.fullName,
        email: deliveryDetails.email,
        phone: deliveryDetails.phone,
        address: deliveryDetails.address,
        city: deliveryDetails.city,
        notes: deliveryDetails.notes,
      }, csrfHeaders());

      if (!checkoutRes.data?.success) throw new Error(checkoutRes.data?.error || 'Failed to create order');

      const { order_number, amount, currency } = checkoutRes.data;
      const normalizedPhone = deliveryDetails.phone.replace(/\s+/g, '').replace(/^0/, '263');

      const paynowRes = await apiClient.post('/crm-api/paynow/initiate-payment/', {
        order_number,
        phone_number: normalizedPhone,
        email: deliveryDetails.email,
        amount: String(amount),
        payment_method: paymentMethod,
        currency: currency || 'USD',
      }, csrfHeaders());

      const d = paynowRes.data || {};
      setPaymentInfo({
        instructions: d.instructions,
        paynow_reference: d.paynow_reference,
        payment_reference: d.payment_reference,
        poll_url: d.poll_url,
        payment_method: d.payment_method || paymentMethod,
        requires_otp: d.requires_otp || false,
        otp_message: d.otp_message,
        authorization_code: d.authorization_code,
        authorization_expires: d.authorization_expires,
        deeplink: d.deeplink,
        redirect_url: d.redirect_url,
      });
      setStep('pay');
    } catch (err: any) {
      setError(err?.response?.data?.message || err?.message || 'Failed to place order. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const submitOTP = async () => {
    if (!otpCode || !paymentInfo?.payment_reference) {
      setError('Please enter the OTP code');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const res = await apiClient.post('/crm-api/paynow/submit-otp/', {
        payment_reference: paymentInfo.payment_reference,
        otp_code: otpCode,
      }, csrfHeaders());
      if (res.data?.success) {
        setOtpCode('');
        // Don't jump straight to "success" - the OTP submission only authorizes
        // the payment, it doesn't confirm funds were actually received. Let the
        // status poll (already running for the 'pay' step) confirm completion.
      } else {
        setError(res.data?.message || 'Failed to submit OTP');
      }
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Failed to submit OTP');
    } finally {
      setSubmitting(false);
    }
  };

  const stopPolling = useCallback(() => {
    if (pollIntervalRef.current) { clearInterval(pollIntervalRef.current); pollIntervalRef.current = null; }
    if (pollTimeoutRef.current) { clearTimeout(pollTimeoutRef.current); pollTimeoutRef.current = null; }
  }, []);

  // Poll the backend for real payment confirmation while on the 'pay' step.
  // A mobile-money push can take anywhere from seconds to a couple of minutes
  // to be authorized, so we can't assume success just because the user clicked
  // a "done" button - only the backend (via Paynow's IPN or its own poll) knows
  // whether money actually moved.
  useEffect(() => {
    if (step !== 'pay' || !paymentInfo?.payment_reference) {
      stopPolling();
      return;
    }

    // Guards state updates from an in-flight request that resolves after this
    // effect has been cleaned up (unmount, step change, or reference change),
    // which would otherwise call setState on a stale/unmounted run.
    let active = true;
    setPaymentPollStatus('pending');

    const checkStatus = async () => {
      try {
        const res = await apiClient.get(`/crm-api/paynow/payment-status/${paymentInfo.payment_reference}/`);
        if (!active) return;
        const s = res.data?.status;
        if (s === 'paid') {
          setPaymentPollStatus('paid');
          stopPolling();
          setStep('success');
        } else if (s === 'failed') {
          setPaymentPollStatus('failed');
          stopPolling();
        }
        // 'pending' -> keep polling
      } catch {
        // Transient network/API error - keep polling until timeout.
      }
    };

    checkStatus();
    pollIntervalRef.current = setInterval(checkStatus, PAYMENT_POLL_INTERVAL_MS);
    pollTimeoutRef.current = setTimeout(() => {
      if (active) {
        setPaymentPollStatus((prev) => (prev === 'pending' ? 'timeout' : prev));
        stopPolling();
      }
    }, PAYMENT_POLL_TIMEOUT_MS);

    return () => {
      active = false;
      stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, paymentInfo?.payment_reference, stopPolling]);

  const isEmpty = !cart || cart.items.length === 0;

  if (cartLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-white via-purple-50 to-sky-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500 font-medium">Loading your cart…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-purple-50/30 to-sky-50/30">
      {/* Top bar */}
      <div className="bg-white border-b border-purple-100 shadow-sm sticky top-0 z-40">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between gap-4">
          <button
            onClick={() => router.push('/shop')}
            className="flex items-center gap-2 text-purple-600 hover:text-purple-800 font-semibold text-sm transition"
          >
            <FiArrowLeft className="w-4 h-4" />
            Back to Shop
          </button>

          <div className="flex-1 flex justify-center">
            <StepIndicator step={step} />
          </div>

          <div className="flex items-center gap-1.5 text-xs text-gray-400 font-medium">
            <FiLock className="w-3.5 h-3.5 text-green-500" />
            Secure Checkout
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {/* Empty cart guard */}
        {isEmpty && step !== 'success' && (
          <div className="text-center py-20">
            <div className="w-20 h-20 rounded-full bg-purple-50 flex items-center justify-center mx-auto mb-4">
              <FiShoppingCart className="w-10 h-10 text-purple-300" />
            </div>
            <h2 className="text-xl font-extrabold text-purple-900 mb-2">Your cart is empty</h2>
            <p className="text-gray-500 mb-6">Add products to your cart before checking out.</p>
            <button
              onClick={() => router.push('/shop')}
              className="px-6 py-3 bg-purple-600 text-white rounded-xl font-bold hover:bg-purple-700 transition"
            >
              Browse Products
            </button>
          </div>
        )}

        {/* Checkout layout */}
        {(!isEmpty || step === 'success') && (
          <div className="grid lg:grid-cols-[1fr_380px] gap-8 items-start">
            {/* Left — form area */}
            <div>
              {error && (
                <div className="mb-5 flex items-center gap-2.5 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm font-medium">
                  <FiAlertCircle className="w-4 h-4 flex-shrink-0" />
                  {error}
                </div>
              )}

              {/* ── STEP: details ── */}
              {step === 'details' && (
                <div className="bg-white rounded-2xl border border-purple-100 shadow-sm p-6 space-y-6">
                  <h2 className="text-xl font-extrabold text-purple-900">Delivery & Payment</h2>

                  {/* Payment method */}
                  <div>
                    <label className="block text-sm font-bold text-purple-900 mb-3">Payment Method</label>
                    <div className="grid grid-cols-2 gap-3">
                      {PAYMENT_METHODS.map((m) => (
                        <button
                          key={m.value}
                          onClick={() => setPaymentMethod(m.value)}
                          className={`p-4 rounded-xl border-2 text-left transition-all ${
                            paymentMethod === m.value
                              ? 'border-purple-600 bg-purple-50 shadow-sm'
                              : 'border-gray-200 bg-white hover:border-purple-200 hover:bg-purple-50/50'
                          }`}
                        >
                          <div className="text-xl mb-1">{m.icon}</div>
                          <p className={`font-bold text-sm ${paymentMethod === m.value ? 'text-purple-800' : 'text-gray-700'}`}>
                            {m.label}
                          </p>
                          <p className="text-xs text-gray-500 mt-0.5">{m.description}</p>
                        </button>
                      ))}
                    </div>
                    <p className="mt-2 text-xs text-gray-400">A secure Paynow request will be sent to your wallet.</p>
                  </div>

                  {/* Delivery fields */}
                  <div className="space-y-4">
                    <h3 className="text-sm font-bold text-purple-900">Delivery Details</h3>

                    {([
                      { name: 'fullName', label: 'Full Name', type: 'text', placeholder: 'John Doe', required: true },
                      { name: 'email', label: 'Email Address', type: 'email', placeholder: 'john@example.com', required: true },
                      { name: 'phone', label: 'Phone Number', type: 'tel', placeholder: '0771234567 or 263771234567', required: true, hint: 'Starts with 0? We auto-format to +263.' },
                      { name: 'address', label: 'Delivery Address', type: 'text', placeholder: '123 Main St, Harare', required: true },
                      { name: 'city', label: 'City', type: 'text', placeholder: 'Harare', required: false },
                    ] as const).map((field) => (
                      <div key={field.name}>
                        <label className="block text-sm font-semibold text-gray-700 mb-1.5">
                          {field.label} {field.required && <span className="text-red-500">*</span>}
                        </label>
                        <input
                          type={field.type}
                          name={field.name}
                          value={deliveryDetails[field.name]}
                          onChange={handleFieldChange}
                          placeholder={field.placeholder}
                          className={`w-full px-4 py-3 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 transition ${
                            fieldErrors[field.name] ? 'border-red-400 bg-red-50' : 'border-gray-200 bg-white hover:border-purple-200'
                          }`}
                        />
                        {'hint' in field && field.hint && !fieldErrors[field.name] && (
                          <p className="mt-1 text-xs text-gray-400">{field.hint}</p>
                        )}
                        <FieldError msg={fieldErrors[field.name]} />
                      </div>
                    ))}

                    <div>
                      <label className="block text-sm font-semibold text-gray-700 mb-1.5">Additional Notes</label>
                      <textarea
                        name="notes"
                        value={deliveryDetails.notes}
                        onChange={handleFieldChange}
                        rows={3}
                        placeholder="Special delivery instructions, colour preferences, etc."
                        className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 transition hover:border-purple-200 resize-none"
                      />
                    </div>
                  </div>

                  {/* Terms of service agreement */}
                  <div className={`rounded-xl border p-4 transition-colors ${termsError ? 'border-red-300 bg-red-50' : 'border-gray-200 bg-gray-50'}`}>
                    <label className="flex items-start gap-3 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        checked={agreedToTerms}
                        onChange={(e) => { setAgreedToTerms(e.target.checked); setTermsError(false); }}
                        className="mt-0.5 w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-400 flex-shrink-0 cursor-pointer"
                      />
                      <span className="text-sm text-gray-600 leading-relaxed">
                        I agree to the{' '}
                        <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:text-purple-800 font-semibold underline underline-offset-2">
                          Terms of Service
                        </a>
                        {' '}and{' '}
                        <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-purple-600 hover:text-purple-800 font-semibold underline underline-offset-2">
                          Privacy Policy
                        </a>
                        . I understand my order will be processed and payment collected via Paynow.
                      </span>
                    </label>
                    {termsError && (
                      <p className="mt-2 text-xs text-red-600 flex items-center gap-1">
                        <FiAlertCircle className="w-3 h-3 flex-shrink-0" />
                        You must agree to the terms before proceeding.
                      </p>
                    )}
                  </div>

                  <button
                    onClick={handleProceedToConfirm}
                    className="w-full py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold text-base transition shadow-sm"
                  >
                    Review Order →
                  </button>
                </div>
              )}

              {/* ── STEP: confirm ── */}
              {step === 'confirm' && cart && (
                <div className="bg-white rounded-2xl border border-purple-100 shadow-sm p-6 space-y-6">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setStep('details')}
                      className="p-2 rounded-xl hover:bg-purple-50 text-purple-600 transition"
                    >
                      <FiArrowLeft className="w-4 h-4" />
                    </button>
                    <h2 className="text-xl font-extrabold text-purple-900">Review Your Order</h2>
                  </div>

                  <div className="bg-purple-50 rounded-xl p-5 border border-purple-100">
                    <p className="text-xs font-bold text-purple-500 uppercase tracking-wider mb-3">Delivery Details</p>
                    <div className="space-y-2 text-sm">
                      {[
                        ['Name', deliveryDetails.fullName],
                        ['Email', deliveryDetails.email],
                        ['Phone', deliveryDetails.phone],
                        ['Address', deliveryDetails.address],
                        deliveryDetails.city && ['City', deliveryDetails.city],
                        deliveryDetails.notes && ['Notes', deliveryDetails.notes],
                        ['Payment', paymentMethod.charAt(0).toUpperCase() + paymentMethod.slice(1)],
                      ].filter(Boolean).map(([label, val]) => (
                        <div key={label as string} className="flex gap-3">
                          <span className="text-gray-400 w-20 flex-shrink-0 font-medium">{label}:</span>
                          <span className="text-gray-800 font-semibold">{val as string}</span>
                        </div>
                      ))}
                    </div>
                    <button
                      onClick={() => setStep('details')}
                      className="mt-3 text-xs text-purple-600 font-semibold hover:underline"
                    >
                      Edit details
                    </button>
                  </div>

                  <div>
                    <p className="text-xs font-bold text-purple-500 uppercase tracking-wider mb-3">Order Items</p>
                    <div className="space-y-2">
                      {cart.items.map((item) => (
                        <div key={item.id} className="flex justify-between items-center text-sm py-2 border-b border-gray-100 last:border-0">
                          <div className="flex items-center gap-2">
                            <span className="w-6 h-6 bg-orange-100 text-orange-600 rounded-full text-xs font-bold flex items-center justify-center flex-shrink-0">
                              {item.quantity}
                            </span>
                            <span className="text-gray-700 font-medium">{item.product.name}</span>
                          </div>
                          <span className="font-bold text-orange-500">{item.product.currency} {parseFloat(item.subtotal).toFixed(2)}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="border-t border-purple-100 pt-4 flex items-center justify-between">
                    <span className="font-semibold text-gray-700">Total</span>
                    <span className="text-2xl font-extrabold text-orange-500">USD {parseFloat(cart.total_price).toFixed(2)}</span>
                  </div>

                  {error && (
                    <div className="flex items-center gap-2 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
                      <FiAlertCircle className="w-4 h-4 flex-shrink-0" />{error}
                    </div>
                  )}

                  <button
                    onClick={placeOrder}
                    disabled={submitting}
                    className="w-full py-4 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold text-base transition shadow-sm disabled:bg-gray-300 flex items-center justify-center gap-2"
                  >
                    <FiLock className="w-4 h-4" />
                    {submitting ? 'Processing…' : 'Pay with Paynow'}
                  </button>
                </div>
              )}

              {/* ── STEP: pay ── */}
              {step === 'pay' && (
                <div className="bg-white rounded-2xl border border-purple-100 shadow-sm p-6 space-y-5">
                  <div className="text-center py-4">
                    <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                      <FiCheck className="w-8 h-8 text-green-600" />
                    </div>
                    <h2 className="text-2xl font-extrabold text-purple-900 mb-1">Payment Initiated!</h2>
                    <p className="text-gray-500 text-sm">Your order has been created. Complete payment below.</p>
                  </div>

                  {paymentInfo?.paynow_reference && (
                    <div className="bg-sky-50 rounded-xl p-4 border border-sky-200 text-center">
                      <p className="text-xs text-sky-500 font-semibold uppercase tracking-wider mb-1">Paynow Reference</p>
                      <p className="font-mono font-extrabold text-sky-900 text-2xl tracking-wider">{paymentInfo.paynow_reference}</p>
                    </div>
                  )}

                  {paymentInfo?.instructions && (
                    <div className="bg-blue-50 rounded-xl p-5 border border-blue-100">
                      <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-2">Instructions</p>
                      <p className="text-gray-700 text-sm whitespace-pre-line leading-relaxed">{paymentInfo.instructions}</p>
                    </div>
                  )}

                  {/* Omari OTP */}
                  {paymentInfo?.requires_otp && (
                    <div className="bg-orange-50 border border-orange-200 rounded-xl p-5">
                      <p className="text-base font-bold text-orange-900 mb-3">Omari OTP Required</p>
                      {paymentInfo.authorization_code && (
                        <div className="bg-white border-2 border-orange-400 rounded-xl p-4 text-center mb-4">
                          <p className="text-xs text-orange-500 uppercase tracking-wider mb-1">Authorization Code</p>
                          <p className="text-3xl font-extrabold text-orange-900 font-mono">{paymentInfo.authorization_code}</p>
                          {paymentInfo.authorization_expires && (
                            <p className="text-xs text-orange-500 mt-1">Expires: {paymentInfo.authorization_expires}</p>
                          )}
                        </div>
                      )}
                      <p className="text-sm text-orange-800 mb-3">{paymentInfo.otp_message || 'Enter the OTP sent to your Omari phone.'}</p>
                      {error && <p className="text-xs text-red-600 mb-2">{error}</p>}
                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={otpCode}
                          onChange={(e) => { setOtpCode(e.target.value); setError(null); }}
                          placeholder="Enter OTP"
                          maxLength={6}
                          className="flex-1 px-4 py-3 border border-orange-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
                        />
                        <button
                          onClick={submitOTP}
                          disabled={submitting || !otpCode}
                          className="px-5 py-3 bg-orange-500 text-white rounded-xl font-bold text-sm hover:bg-orange-600 disabled:bg-gray-300 transition"
                        >
                          {submitting ? '…' : 'Submit'}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Innbucks */}
                  {paymentInfo?.payment_method === 'innbucks' && paymentInfo.authorization_code && !paymentInfo.requires_otp && (
                    <div className="bg-purple-50 border border-purple-200 rounded-xl p-5">
                      <p className="text-base font-bold text-purple-900 mb-3">Innbucks Authorization</p>
                      <div className="bg-white border-2 border-purple-400 rounded-xl p-4 text-center mb-4">
                        <p className="text-xs text-purple-500 uppercase tracking-wider mb-1">Authorization Code</p>
                        <p className="text-4xl font-extrabold text-purple-900 font-mono tracking-wider">{paymentInfo.authorization_code}</p>
                        {paymentInfo.authorization_expires && (
                          <p className="text-xs text-purple-500 mt-1">Expires: {paymentInfo.authorization_expires}</p>
                        )}
                      </div>
                      <ol className="text-sm text-purple-700 space-y-1.5 ml-4 list-decimal">
                        <li>Open your Innbucks wallet app</li>
                        <li>Go to "Authorize Payment"</li>
                        <li>Enter the code above</li>
                        <li>Confirm the payment</li>
                      </ol>
                      {paymentInfo.deeplink && (
                        <a href={paymentInfo.deeplink} target="_blank" rel="noopener noreferrer"
                          className="mt-4 flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-xl font-bold text-sm hover:bg-purple-700 transition">
                          Open Innbucks App
                        </a>
                      )}
                    </div>
                  )}

                  {/* Live payment confirmation status */}
                  {paymentPollStatus === 'pending' && (
                    <div className="bg-sky-50 border border-sky-100 rounded-xl p-4 flex items-center gap-3">
                      <div className="w-5 h-5 border-2 border-sky-300 border-t-sky-600 rounded-full animate-spin flex-shrink-0" />
                      <p className="text-sm text-sky-700 font-medium">
                        Waiting for payment confirmation… Approve the prompt on your phone.
                      </p>
                    </div>
                  )}
                  {paymentPollStatus === 'failed' && (
                    <div className="bg-red-50 border border-red-200 rounded-xl p-4">
                      <p className="text-sm text-red-700 font-semibold mb-1">Payment was not completed.</p>
                      <p className="text-xs text-red-600">It may have been cancelled or declined. You can go back and try again, or contact support with your reference above.</p>
                    </div>
                  )}
                  {paymentPollStatus === 'timeout' && (
                    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
                      <p className="text-sm text-amber-700 font-semibold mb-1">Still waiting on confirmation.</p>
                      <p className="text-xs text-amber-600">This is taking longer than usual. You'll get a WhatsApp message once it's confirmed — you can safely leave this page.</p>
                    </div>
                  )}

                  <div className="flex gap-3">
                    {(paymentPollStatus === 'failed' || paymentPollStatus === 'timeout') && (
                      <button
                        onClick={() => { setError(null); setPaymentPollStatus('idle'); setStep('confirm'); }}
                        className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold text-sm transition"
                      >
                        Try Again
                      </button>
                    )}
                    <button
                      onClick={() => router.push('/shop')}
                      className="flex-1 py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl font-bold text-sm transition"
                    >
                      Leave &amp; Check Later
                    </button>
                  </div>
                </div>
              )}

              {/* ── STEP: success ── */}
              {step === 'success' && (
                <div className="bg-white rounded-2xl border border-purple-100 shadow-sm p-10 text-center">
                  <div className="w-24 h-24 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-5 shadow">
                    <FiCheck className="w-12 h-12 text-green-600" />
                  </div>
                  <h2 className="text-3xl font-extrabold text-purple-900 mb-3">Order Confirmed!</h2>
                  <p className="text-gray-500 text-base mb-8 max-w-sm mx-auto leading-relaxed">
                    Thank you for your order. You'll receive a WhatsApp confirmation shortly with your order details and tracking information.
                  </p>
                  <button
                    onClick={() => router.push('/shop')}
                    className="px-10 py-4 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold text-base transition shadow-sm"
                  >
                    Continue Shopping
                  </button>
                </div>
              )}
            </div>

            {/* Right — order summary (hidden on success) */}
            {step !== 'success' && (
              <div className="space-y-4">
                <OrderSummary cart={cart} />
                <div className="bg-white rounded-2xl border border-purple-100 shadow-sm p-4 text-xs text-gray-500 space-y-2">
                  <div className="flex items-center gap-2 font-medium text-gray-600">
                    <FiLock className="w-3.5 h-3.5 text-green-500" /> Secure & Encrypted
                  </div>
                  <p>Your payment is processed securely via Paynow. We never store your card details.</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
