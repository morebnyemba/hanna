'use client';

import { useEffect, useState } from 'react';
import { FiX, FiShoppingCart, FiMessageCircle, FiPackage, FiSun, FiWifi, FiChevronLeft, FiChevronRight, FiBell } from 'react-icons/fi';
import type { Product } from './ProductCard';
import ReviewSection from './ReviewSection';
import RelatedProducts from './RelatedProducts';
import BackInStockModal from './BackInStockModal';

interface ProductDetailModalProps {
  product: Product | null;
  whatsappNumber: string;
  onClose: () => void;
  onAddToCart: (id: number) => void;
  cartLoading: boolean;
  allProducts?: Product[];
  csrfToken?: string | null;
  onSelectProduct?: (product: Product) => void;
}

function PlaceholderIcon({ category }: { category: string | null }) {
  const name = (category || '').toLowerCase();
  if (name.includes('solar') || name.includes('panel')) return <FiSun className="w-16 h-16 text-orange-200" />;
  if (name.includes('starlink') || name.includes('wifi')) return <FiWifi className="w-16 h-16 text-sky-200" />;
  return <FiPackage className="w-16 h-16 text-purple-200" />;
}

function StockBadge({ qty }: { qty: number }) {
  if (qty === 0) return <span className="text-sm font-semibold px-3 py-1 rounded-full bg-red-100 text-red-600">Out of Stock</span>;
  if (qty <= 5) return <span className="text-sm font-semibold px-3 py-1 rounded-full bg-orange-100 text-orange-600">Low Stock ({qty} left)</span>;
  return <span className="text-sm font-semibold px-3 py-1 rounded-full bg-green-100 text-green-700">In Stock</span>;
}

export default function ProductDetailModal({ product, whatsappNumber, onClose, onAddToCart, cartLoading, allProducts = [], csrfToken = null, onSelectProduct }: ProductDetailModalProps) {
  const [imgIdx, setImgIdx] = useState(0);
  const [qty, setQty] = useState(1);
  const [showNotifyModal, setShowNotifyModal] = useState(false);

  useEffect(() => {
    setImgIdx(0);
    setQty(1);
    setShowNotifyModal(false);
  }, [product]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  if (!product) return null;

  const images = product.images || [];
  const price = parseFloat(product.price);
  const waLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(`Hi, I'm interested in: ${product.name}`)}`
    : null;

  return (
    <div className="shop-backdrop-enter fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div className="shop-modal-enter bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-purple-100" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-purple-50">
          <span className="text-xs font-semibold text-purple-500 uppercase tracking-wider">Product Detail</span>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-gray-100 text-gray-500 transition">
            <FiX className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 grid sm:grid-cols-2 gap-6">
          {/* Image area */}
          <div>
            <div className="relative h-56 bg-gradient-to-br from-purple-50 to-sky-50 rounded-xl flex items-center justify-center overflow-hidden mb-3">
              {images.length > 0 ? (
                <img src={images[imgIdx].image} alt={images[imgIdx].alt_text || product.name} className="w-full h-full object-cover" />
              ) : (
                <PlaceholderIcon category={product.category?.name || null} />
              )}
              {images.length > 1 && (
                <>
                  <button onClick={() => setImgIdx((i) => (i - 1 + images.length) % images.length)}
                    className="absolute left-2 top-1/2 -translate-y-1/2 p-1.5 bg-white/80 rounded-full shadow">
                    <FiChevronLeft className="w-4 h-4 text-purple-700" />
                  </button>
                  <button onClick={() => setImgIdx((i) => (i + 1) % images.length)}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 bg-white/80 rounded-full shadow">
                    <FiChevronRight className="w-4 h-4 text-purple-700" />
                  </button>
                </>
              )}
            </div>
            {/* Thumbnails */}
            {images.length > 1 && (
              <div className="flex gap-2 overflow-x-auto">
                {images.map((img, i) => (
                  <button key={img.id} onClick={() => setImgIdx(i)}
                    className={`w-12 h-12 rounded-lg overflow-hidden flex-shrink-0 border-2 transition ${i === imgIdx ? 'border-purple-500' : 'border-transparent'}`}>
                    <img src={img.image} alt={img.alt_text || ''} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex flex-col">
            {product.category && (
              <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-sky-100 text-sky-700 self-start mb-2">{product.category.name}</span>
            )}
            {product.brand && <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{product.brand}</p>}
            <h2 className="text-xl font-extrabold text-purple-900 mb-2 leading-tight">{product.name}</h2>
            <div className="mb-3"><StockBadge qty={product.stock_quantity} /></div>

            <p className="text-3xl font-extrabold text-orange-500 mb-4">
              {product.currency} {isNaN(price) ? '—' : price.toFixed(2)}
            </p>

            {product.description && (
              <p className="text-sm text-gray-600 mb-4 leading-relaxed">{product.description}</p>
            )}

            {/* Metadata */}
            <div className="grid grid-cols-2 gap-2 text-xs mb-4">
              {product.sku && (
                <div className="bg-gray-50 rounded-lg p-2">
                  <p className="text-gray-400 uppercase tracking-wide mb-0.5">SKU</p>
                  <p className="font-semibold text-gray-700">{product.sku}</p>
                </div>
              )}
              {product.product_type && (
                <div className="bg-gray-50 rounded-lg p-2">
                  <p className="text-gray-400 uppercase tracking-wide mb-0.5">Type</p>
                  <p className="font-semibold text-gray-700 capitalize">{product.product_type}</p>
                </div>
              )}
            </div>

            {/* Qty + Add to Cart */}
            <div className="mt-auto space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-gray-600">Qty:</span>
                <div className="flex items-center border border-purple-200 rounded-xl overflow-hidden">
                  <button onClick={() => setQty((q) => Math.max(1, q - 1))}
                    className="px-3 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold transition">−</button>
                  <span className="px-4 py-2 font-bold text-purple-900 min-w-[2.5rem] text-center">{qty}</span>
                  <button onClick={() => setQty((q) => Math.min(product.stock_quantity, q + 1))}
                    className="px-3 py-2 bg-purple-50 hover:bg-purple-100 text-purple-700 font-bold transition">+</button>
                </div>
              </div>

              <button
                onClick={() => { onAddToCart(product.id); onClose(); }}
                disabled={product.stock_quantity === 0 || cartLoading}
                className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-bold text-sm transition disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed shadow"
              >
                <FiShoppingCart className="w-4 h-4" />
                {product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
              </button>

              {product.stock_quantity === 0 && (
                <button
                  onClick={() => setShowNotifyModal(true)}
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 font-semibold text-sm transition"
                >
                  <FiBell className="w-4 h-4" />
                  Notify Me When Available
                </button>
              )}

              {waLink && (
                <a href={waLink} target="_blank" rel="noopener noreferrer"
                  className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-700 border border-sky-200 font-semibold text-sm transition">
                  <FiMessageCircle className="w-4 h-4" />
                  Ask on WhatsApp
                </a>
              )}
            </div>
          </div>
        </div>

        {/* Related Products + Reviews */}
        <div className="px-6 pb-6">
          {allProducts.length > 0 && (
            <RelatedProducts
              currentProduct={product}
              allProducts={allProducts}
              onSelect={(p) => onSelectProduct ? onSelectProduct(p) : onClose()}
              onAddToCart={onAddToCart}
            />
          )}
          <ReviewSection productId={product.id} csrfToken={csrfToken} />
        </div>
      </div>

      {showNotifyModal && (
        <BackInStockModal
          product={product}
          csrfToken={csrfToken}
          onClose={() => setShowNotifyModal(false)}
        />
      )}
    </div>
  );
}
