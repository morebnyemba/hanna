'use client';

import { FiX, FiShoppingCart, FiPackage, FiPlus, FiMinus, FiTrash2 } from 'react-icons/fi';
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

interface CartDrawerProps {
  open: boolean;
  cart: Cart | null;
  cartLoading: boolean;
  clearConfirm: boolean;
  onClose: () => void;
  onUpdateQty: (itemId: number, qty: number) => void;
  onRemove: (itemId: number) => void;
  onClearRequest: () => void;
  onClearConfirm: () => void;
  onClearCancel: () => void;
  onCheckout: () => void;
}

export default function CartDrawer({
  open, cart, cartLoading, clearConfirm,
  onClose, onUpdateQty, onRemove, onClearRequest, onClearConfirm, onClearCancel, onCheckout,
}: CartDrawerProps) {
  if (!open) return null;

  const isEmpty = !cart || cart.items.length === 0;
  const total = cart ? parseFloat(cart.total_price) : 0;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      <div className="shop-backdrop-enter absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      <div className="shop-drawer-enter absolute right-0 top-0 bottom-0 w-full sm:max-w-md bg-white shadow-2xl flex flex-col">
        {/* Header */}
        <div className="px-5 pt-5 pb-4 border-b border-purple-50 bg-white flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FiShoppingCart className="w-5 h-5 text-purple-600" />
            <h2 className="text-lg font-extrabold text-purple-900">Your Cart</h2>
            {!isEmpty && (
              <span className="ml-1 bg-orange-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                {cart!.total_items}
              </span>
            )}
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition">
            <FiX className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-5 py-4">
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
        </div>

        {/* Footer */}
        {!isEmpty && (
          <div className="border-t border-purple-50 px-5 py-4 bg-white space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-600">Order Total</span>
              <span className="text-2xl font-extrabold text-orange-500">USD {total.toFixed(2)}</span>
            </div>
            <button
              onClick={onCheckout}
              disabled={cartLoading}
              className="w-full py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-bold text-sm transition disabled:bg-gray-300 shadow-sm"
            >
              Proceed to Checkout →
            </button>
            <button onClick={onClose} className="w-full text-sm text-purple-600 font-semibold py-1 hover:underline">
              ← Continue Shopping
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
