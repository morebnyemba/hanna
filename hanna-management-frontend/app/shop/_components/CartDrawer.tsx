'use client';

import { FiX, FiShoppingCart, FiPackage, FiPlus, FiMinus, FiTrash2, FiCheck, FiAlertCircle, FiArrowLeft } from 'react-icons/fi';
import type { Product } from './ProductCard';

export interface CartItem {
  id: number;
  product: Product;
  quantity: number;
  subtotal: string;
}

export interface Cart {
  id: number;
  items: CartItem[];
  total_items: number;
  total_price: string;
}

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
  poll_url?: string;
  payment_method?: string;
  requires_otp?: boolean;
  otp_message?: string;
  authorization_code?: string;
  authorization_expires?: string;
  deeplink?: string;
  redirect_url?: string;
}

interface CartDrawerProps {
  open: boolean;
  cart: Cart | null;
  cartLoading: boolean;
  checkoutStep: number;
  deliveryDetails: DeliveryDetails;
  paymentMethod: 'ecocash' | 'omari' | 'innbucks' | 'telecash';
  paymentInfo: PaymentInfo | null;
  otpCode: string;
  fieldErrors: Partial<Record<keyof DeliveryDetails, string>>;
  clearConfirm: boolean;
  onClose: () => void;
  onUpdateQty: (itemId: number, qty: number) => void;
  onRemove: (itemId: number) => void;
  onClearRequest: () => void;
  onClearConfirm: () => void;
  onClearCancel: () => void;
  onDeliveryChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  onPaymentMethodChange: (m: 'ecocash' | 'omari' | 'innbucks' | 'telecash') => void;
  onProceed: () => void;
  onBack: () => void;
  onPlaceOrder: () => void;
  onOtpChange: (v: string) => void;
  onSubmitOTP: () => void;
  onDone: () => void;
}

const STEPS = ['Cart', 'Details', 'Confirm', 'Pay'];

function Stepper({ step }: { step: number }) {
  return (
    <div className="flex items-center gap-1 mt-3">
      {STEPS.map((label, i) => {
        const idx = i + 1;
        const done = step > idx;
        const active = step === idx;
        return (
          <div key={label} className="flex items-center flex-1 last:flex-none">
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border-2 transition flex-shrink-0 ${
              done ? 'bg-orange-500 border-orange-500 text-white' :
              active ? 'bg-purple-600 border-purple-600 text-white' :
              'bg-white border-gray-200 text-gray-400'
            }`}>
              {done ? <FiCheck className="w-3.5 h-3.5" /> : idx}
            </div>
            <span className={`hidden sm:block ml-1 text-xs font-semibold ${active ? 'text-purple-700' : done ? 'text-orange-500' : 'text-gray-400'}`}>
              {label}
            </span>
            {i < STEPS.length - 1 && (
              <div className={`flex-1 h-0.5 mx-2 ${step > idx ? 'bg-orange-400' : step === idx ? 'bg-purple-200' : 'bg-gray-100'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

const PAYMENT_METHODS = [
  { value: 'ecocash', label: 'EcoCash', color: 'bg-green-50 border-green-300 text-green-800' },
  { value: 'omari', label: 'Omari', color: 'bg-sky-50 border-sky-300 text-sky-800' },
  { value: 'innbucks', label: 'Innbucks', color: 'bg-purple-50 border-purple-300 text-purple-800' },
  { value: 'telecash', label: 'Telecash', color: 'bg-orange-50 border-orange-300 text-orange-800' },
] as const;

function FieldError({ msg }: { msg?: string }) {
  if (!msg) return null;
  return <p className="mt-1 text-xs text-red-600 flex items-center gap-1"><FiAlertCircle className="w-3 h-3" />{msg}</p>;
}

export default function CartDrawer({
  open, cart, cartLoading, checkoutStep,
  deliveryDetails, paymentMethod, paymentInfo, otpCode,
  fieldErrors, clearConfirm,
  onClose, onUpdateQty, onRemove, onClearRequest, onClearConfirm, onClearCancel,
  onDeliveryChange, onPaymentMethodChange, onProceed, onBack, onPlaceOrder,
  onOtpChange, onSubmitOTP, onDone,
}: CartDrawerProps) {
  if (!open) return null;

  const isEmpty = !cart || cart.items.length === 0;
  const total = cart ? parseFloat(cart.total_price) : 0;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="shop-backdrop-enter absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={() => { onClose(); }}
      />

      {/* Drawer */}
      <div className="shop-drawer-enter absolute right-0 top-0 bottom-0 w-full sm:max-w-md bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-purple-50 bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {checkoutStep > 1 && (
                <button onClick={onBack} className="p-1.5 rounded-lg hover:bg-purple-50 text-purple-600 transition mr-1">
                  <FiArrowLeft className="w-4 h-4" />
                </button>
              )}
              <h2 className="text-lg font-extrabold text-purple-900">
                {checkoutStep === 1 && 'Your Cart'}
                {checkoutStep === 2 && 'Delivery & Payment'}
                {checkoutStep === 3 && 'Confirm Order'}
                {checkoutStep === 4 && 'Payment'}
                {checkoutStep === 5 && 'Order Placed!'}
              </h2>
            </div>
            <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition">
              <FiX className="w-5 h-5" />
            </button>
          </div>
          <Stepper step={Math.min(checkoutStep, 4)} />
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">

          {/* ── STEP 1: Cart items ── */}
          {checkoutStep === 1 && (
            <>
              {isEmpty ? (
                <div className="flex flex-col items-center justify-center h-full py-16 text-center">
                  <div className="w-16 h-16 rounded-full bg-purple-50 flex items-center justify-center mb-4">
                    <FiShoppingCart className="w-8 h-8 text-purple-300" />
                  </div>
                  <p className="text-gray-700 font-semibold">Your cart is empty</p>
                  <p className="text-gray-400 text-sm mt-1">Add some products to get started</p>
                  <button onClick={onClose} className="mt-4 text-purple-600 text-sm font-semibold hover:underline">
                    Continue Shopping
                  </button>
                </div>
              ) : (
                <div className="space-y-3">
                  {cart!.items.map((item) => (
                    <div key={item.id} className="flex items-start gap-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                      <div className="w-14 h-14 bg-gradient-to-br from-purple-50 to-sky-50 rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
                        {item.product.images && item.product.images.length > 0 ? (
                          <img src={item.product.images[0].image} alt={item.product.name} className="w-full h-full object-cover" />
                        ) : (
                          <FiPackage className="w-6 h-6 text-purple-300" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-purple-900 text-sm leading-snug line-clamp-2">{item.product.name}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{item.product.currency} {parseFloat(item.product.price).toFixed(2)} each</p>
                        <div className="flex items-center gap-1.5 mt-2">
                          <button
                            onClick={() => onUpdateQty(item.id, item.quantity - 1)}
                            disabled={cartLoading || item.quantity <= 1}
                            className="w-6 h-6 rounded-md bg-purple-100 hover:bg-purple-200 text-purple-700 flex items-center justify-center disabled:opacity-40 transition"
                          >
                            <FiMinus className="w-3 h-3" />
                          </button>
                          <span className="font-bold text-purple-900 w-7 text-center text-sm">{item.quantity}</span>
                          <button
                            onClick={() => onUpdateQty(item.id, item.quantity + 1)}
                            disabled={cartLoading || item.quantity >= item.product.stock_quantity}
                            className="w-6 h-6 rounded-md bg-purple-100 hover:bg-purple-200 text-purple-700 flex items-center justify-center disabled:opacity-40 transition"
                          >
                            <FiPlus className="w-3 h-3" />
                          </button>
                          <button
                            onClick={() => onRemove(item.id)}
                            disabled={cartLoading}
                            className="ml-auto p-1 text-red-400 hover:bg-red-50 rounded-md transition"
                          >
                            <FiTrash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <p className="font-extrabold text-orange-500 text-sm flex-shrink-0">
                        {item.product.currency} {parseFloat(item.subtotal).toFixed(2)}
                      </p>
                    </div>
                  ))}

                  {/* Clear cart confirm */}
                  {clearConfirm ? (
                    <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-center">
                      <p className="text-sm font-semibold text-red-700 mb-3">Clear all items?</p>
                      <div className="flex gap-2 justify-center">
                        <button onClick={onClearConfirm} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-semibold hover:bg-red-700 transition">
                          Yes, clear
                        </button>
                        <button onClick={onClearCancel} className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm font-semibold hover:bg-gray-200 transition">
                          Keep
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button onClick={onClearRequest} className="w-full text-red-500 text-sm font-medium py-2 hover:bg-red-50 rounded-lg transition">
                      Remove all items
                    </button>
                  )}
                </div>
              )}
            </>
          )}

          {/* ── STEP 2: Delivery + Payment method ── */}
          {checkoutStep === 2 && (
            <div className="space-y-4">
              {/* Payment method */}
              <div>
                <label className="block text-sm font-bold text-purple-900 mb-2">Payment Method</label>
                <div className="grid grid-cols-2 gap-2">
                  {PAYMENT_METHODS.map((m) => (
                    <button
                      key={m.value}
                      onClick={() => onPaymentMethodChange(m.value)}
                      className={`py-3 px-3 rounded-xl border-2 font-bold text-sm transition ${
                        paymentMethod === m.value
                          ? 'border-purple-600 bg-purple-50 text-purple-800 shadow-sm'
                          : 'border-gray-200 bg-white text-gray-600 hover:border-purple-200'
                      }`}
                    >
                      {m.label}
                    </button>
                  ))}
                </div>
                <p className="mt-1.5 text-xs text-gray-400">Secure Paynow request will be sent to your wallet.</p>
              </div>

              {/* Fields */}
              {([
                { name: 'fullName', label: 'Full Name', type: 'text', placeholder: 'John Doe', required: true },
                { name: 'email', label: 'Email', type: 'email', placeholder: 'john@example.com', required: true },
                { name: 'phone', label: 'Phone Number', type: 'tel', placeholder: '0771234567 or 263771234567', required: true, hint: 'Starts with 0? We auto-format to +263.' },
                { name: 'address', label: 'Delivery Address', type: 'text', placeholder: '123 Main St', required: true },
                { name: 'city', label: 'City', type: 'text', placeholder: 'Harare', required: false },
              ] as const).map((field) => (
                <div key={field.name}>
                  <label className="block text-sm font-semibold text-gray-700 mb-1">
                    {field.label} {field.required && <span className="text-red-500">*</span>}
                  </label>
                  <input
                    type={field.type}
                    name={field.name}
                    value={deliveryDetails[field.name]}
                    onChange={onDeliveryChange}
                    placeholder={field.placeholder}
                    className={`w-full px-4 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 transition ${
                      fieldErrors[field.name] ? 'border-red-400 bg-red-50' : 'border-gray-200 bg-white'
                    }`}
                  />
                  {'hint' in field && field.hint && !fieldErrors[field.name] && (
                    <p className="mt-1 text-xs text-gray-400">{field.hint}</p>
                  )}
                  <FieldError msg={fieldErrors[field.name]} />
                </div>
              ))}

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-1">Additional Notes</label>
                <textarea
                  name="notes"
                  value={deliveryDetails.notes}
                  onChange={onDeliveryChange}
                  rows={3}
                  placeholder="Special delivery instructions, colour preferences, etc."
                  className="w-full px-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-purple-400 transition"
                />
              </div>
            </div>
          )}

          {/* ── STEP 3: Confirmation ── */}
          {checkoutStep === 3 && cart && (
            <div className="space-y-5">
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
                <p className="text-xs font-bold text-purple-500 uppercase tracking-wider mb-3">Delivery Details</p>
                <div className="space-y-1.5 text-sm">
                  {[
                    ['Name', deliveryDetails.fullName],
                    ['Email', deliveryDetails.email],
                    ['Phone', deliveryDetails.phone],
                    ['Address', deliveryDetails.address],
                    deliveryDetails.city && ['City', deliveryDetails.city],
                    deliveryDetails.notes && ['Notes', deliveryDetails.notes],
                  ].filter(Boolean).map(([label, val]) => (
                    <div key={label} className="flex gap-2">
                      <span className="text-gray-500 w-16 flex-shrink-0">{label}:</span>
                      <span className="text-gray-900 font-medium">{val}</span>
                    </div>
                  ))}
                  <div className="flex gap-2 pt-1 border-t border-purple-200 mt-2">
                    <span className="text-gray-500 w-16 flex-shrink-0">Payment:</span>
                    <span className="text-gray-900 font-semibold capitalize">{paymentMethod}</span>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-xs font-bold text-purple-500 uppercase tracking-wider mb-3">Order Items</p>
                <div className="space-y-2">
                  {cart.items.map((item) => (
                    <div key={item.id} className="flex justify-between text-sm py-1.5 border-b border-gray-100 last:border-0">
                      <span className="text-gray-700">{item.quantity}× {item.product.name}</span>
                      <span className="font-bold text-orange-500">{item.product.currency} {parseFloat(item.subtotal).toFixed(2)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── STEP 4: Payment instructions ── */}
          {checkoutStep === 4 && (
            <div className="space-y-5">
              <div className="text-center py-4">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-3">
                  <FiCheck className="w-8 h-8 text-green-600" />
                </div>
                <h3 className="text-xl font-extrabold text-purple-900 mb-1">Payment Initiated!</h3>
                <p className="text-gray-500 text-sm">Your order has been created. Complete payment below.</p>
              </div>

              {paymentInfo?.paynow_reference && (
                <div className="bg-sky-50 rounded-xl p-4 border border-sky-200">
                  <p className="text-xs text-sky-500 font-semibold uppercase tracking-wider mb-1">Paynow Reference</p>
                  <p className="font-mono font-extrabold text-sky-900 text-lg">{paymentInfo.paynow_reference}</p>
                </div>
              )}

              {paymentInfo?.instructions && (
                <div className="bg-blue-50 rounded-xl p-4 border border-blue-100">
                  <p className="text-xs font-bold text-blue-600 uppercase tracking-wider mb-2">Instructions</p>
                  <p className="text-gray-700 text-sm whitespace-pre-line leading-relaxed">{paymentInfo.instructions}</p>
                </div>
              )}

              {/* Omari OTP */}
              {paymentInfo?.requires_otp && (
                <div className="bg-orange-50 border border-orange-200 rounded-xl p-4">
                  <p className="text-sm font-bold text-orange-900 mb-3">Omari OTP Required</p>
                  {paymentInfo.authorization_code && (
                    <div className="bg-white border-2 border-orange-400 rounded-xl p-3 text-center mb-3">
                      <p className="text-xs text-orange-500 uppercase tracking-wider mb-1">Authorization Code</p>
                      <p className="text-2xl font-extrabold text-orange-900 font-mono">{paymentInfo.authorization_code}</p>
                      {paymentInfo.authorization_expires && (
                        <p className="text-xs text-orange-500 mt-1">Expires: {paymentInfo.authorization_expires}</p>
                      )}
                    </div>
                  )}
                  <p className="text-sm text-orange-800 mb-3">{paymentInfo.otp_message || 'Enter the OTP sent to your Omari phone.'}</p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={otpCode}
                      onChange={(e) => onOtpChange(e.target.value)}
                      placeholder="Enter OTP"
                      maxLength={6}
                      className="flex-1 px-4 py-2.5 border border-orange-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-orange-400 text-sm"
                    />
                    <button
                      onClick={onSubmitOTP}
                      disabled={cartLoading || !otpCode}
                      className="px-5 py-2.5 bg-orange-500 text-white rounded-xl font-bold text-sm hover:bg-orange-600 disabled:bg-gray-300 transition"
                    >
                      Submit
                    </button>
                  </div>
                </div>
              )}

              {/* Innbucks */}
              {paymentInfo?.payment_method === 'innbucks' && paymentInfo.authorization_code && (
                <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
                  <p className="text-sm font-bold text-purple-900 mb-3">Innbucks Authorization</p>
                  <div className="bg-white border-2 border-purple-400 rounded-xl p-4 text-center mb-3">
                    <p className="text-xs text-purple-500 uppercase tracking-wider mb-1">Authorization Code</p>
                    <p className="text-3xl font-extrabold text-purple-900 font-mono tracking-wider">{paymentInfo.authorization_code}</p>
                    {paymentInfo.authorization_expires && (
                      <p className="text-xs text-purple-500 mt-1">Expires: {paymentInfo.authorization_expires}</p>
                    )}
                  </div>
                  <ol className="text-sm text-purple-700 space-y-1 ml-4 list-decimal">
                    <li>Open your Innbucks wallet app</li>
                    <li>Go to "Authorize Payment"</li>
                    <li>Enter the code above</li>
                    <li>Confirm the payment</li>
                  </ol>
                  {paymentInfo.deeplink && (
                    <a href={paymentInfo.deeplink} target="_blank" rel="noopener noreferrer"
                      className="mt-3 flex items-center justify-center px-4 py-2.5 bg-purple-600 text-white rounded-xl font-bold text-sm hover:bg-purple-700 transition">
                      Open Innbucks App
                    </a>
                  )}
                </div>
              )}

              <div className="bg-sky-50 border border-sky-100 rounded-xl p-4">
                <p className="text-sm text-sky-700 font-medium">
                  💬 You will receive a WhatsApp confirmation message once payment is complete.
                </p>
              </div>
            </div>
          )}

          {/* ── STEP 5: Success ── */}
          {checkoutStep === 5 && (
            <div className="flex flex-col items-center justify-center h-full py-12 text-center">
              <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mb-5 shadow">
                <FiCheck className="w-10 h-10 text-green-600" />
              </div>
              <h3 className="text-2xl font-extrabold text-purple-900 mb-2">Order Confirmed!</h3>
              <p className="text-gray-500 text-sm mb-6 max-w-xs">
                Thank you for your order. You'll receive a WhatsApp confirmation shortly with your order details.
              </p>
              <button onClick={onDone} className="px-8 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold transition shadow">
                Continue Shopping
              </button>
            </div>
          )}
        </div>

        {/* Footer actions */}
        {!isEmpty && checkoutStep < 5 && (
          <div className="border-t border-purple-50 px-5 py-4 bg-white space-y-3">
            {/* Total */}
            {cart && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-600">Order Total</span>
                <span className="text-2xl font-extrabold text-orange-500">
                  USD {total.toFixed(2)}
                </span>
              </div>
            )}

            <div className="flex gap-2">
              {checkoutStep < 3 && (
                <button
                  onClick={onProceed}
                  disabled={cartLoading}
                  className="flex-1 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold text-sm transition disabled:bg-gray-300 shadow-sm"
                >
                  {cartLoading ? 'Loading…' : checkoutStep === 1 ? 'Proceed to Checkout' : 'Continue'}
                </button>
              )}
              {checkoutStep === 3 && (
                <button
                  onClick={onPlaceOrder}
                  disabled={cartLoading}
                  className="flex-1 py-3 bg-orange-500 hover:bg-orange-600 text-white rounded-xl font-bold text-sm transition disabled:bg-gray-300 shadow-sm"
                >
                  {cartLoading ? 'Processing…' : '🔒 Pay with Paynow'}
                </button>
              )}
              {checkoutStep === 4 && (
                <button
                  onClick={onDone}
                  className="flex-1 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold text-sm transition"
                >
                  Done
                </button>
              )}
            </div>

            {checkoutStep === 1 && (
              <button onClick={onClose} className="w-full text-sm text-purple-600 font-semibold py-1 hover:underline">
                ← Continue Shopping
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
