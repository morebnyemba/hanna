'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { FiChevronLeft, FiChevronRight, FiShoppingCart, FiMessageCircle, FiSun, FiWifi, FiPackage } from 'react-icons/fi';
import type { Product } from './ProductCard';

interface HeroCarouselProps {
  products: Product[];
  whatsappNumber: string;
  onAddToCart: (id: number) => void;
  onQuickView: (product: Product) => void;
  cartLoading: boolean;
}

function categoryGradient(category: string | null) {
  const n = (category || '').toLowerCase();
  if (n.includes('solar') || n.includes('panel') || n.includes('battery'))
    return { from: 'from-orange-600', to: 'to-amber-500', badge: 'bg-orange-500', text: 'text-orange-100' };
  if (n.includes('starlink') || n.includes('wifi') || n.includes('internet'))
    return { from: 'from-sky-700', to: 'to-blue-500', badge: 'bg-sky-500', text: 'text-sky-100' };
  if (n.includes('furniture') || n.includes('bedroom') || n.includes('kitchen') || n.includes('fitted') || n.includes('luxury'))
    return { from: 'from-purple-700', to: 'to-violet-500', badge: 'bg-purple-500', text: 'text-purple-100' };
  return { from: 'from-purple-800', to: 'to-sky-600', badge: 'bg-purple-500', text: 'text-purple-100' };
}

function PlaceholderIcon({ category }: { category: string | null }) {
  const n = (category || '').toLowerCase();
  if (n.includes('solar') || n.includes('panel')) return <FiSun className="w-24 h-24 text-white/30" />;
  if (n.includes('starlink') || n.includes('wifi')) return <FiWifi className="w-24 h-24 text-white/30" />;
  return <FiPackage className="w-24 h-24 text-white/30" />;
}

export default function HeroCarousel({ products, whatsappNumber, onAddToCart, onQuickView, cartLoading }: HeroCarouselProps) {
  const [idx, setIdx] = useState(0);
  const [animating, setAnimating] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const slides = products.filter((p) => p.is_active).slice(0, 10);

  const go = useCallback((next: number) => {
    if (animating || slides.length === 0) return;
    setAnimating(true);
    setTimeout(() => {
      setIdx(next);
      setAnimating(false);
    }, 300);
  }, [animating, slides.length]);

  const prev = useCallback(() => go((idx - 1 + slides.length) % slides.length), [go, idx, slides.length]);
  const next = useCallback(() => go((idx + 1) % slides.length), [go, idx, slides.length]);

  useEffect(() => {
    if (slides.length < 2) return;
    timerRef.current = setInterval(next, 5000);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [next, slides.length]);

  const resetTimer = () => {
    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(next, 5000);
  };

  if (slides.length === 0) return null;

  const product = slides[idx];
  const cat = product.category?.name || null;
  const g = categoryGradient(cat);
  const price = parseFloat(product.price);
  const waLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(`Hi, I'm interested in: ${product.name}`)}`
    : null;

  return (
    <section className="relative mb-8 rounded-2xl overflow-hidden shadow-lg" style={{ minHeight: '380px' }}>
      {/* Slide */}
      <div
        className={`absolute inset-0 bg-gradient-to-br ${g.from} ${g.to} transition-opacity duration-300 ${animating ? 'opacity-0' : 'opacity-100'}`}
      />

      {/* Background image blur */}
      {product.images && product.images.length > 0 && (
        <div
          className={`absolute inset-0 transition-opacity duration-300 ${animating ? 'opacity-0' : 'opacity-20'}`}
          style={{
            backgroundImage: `url(${product.images[0].image})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            filter: 'blur(12px)',
            transform: 'scale(1.1)',
          }}
        />
      )}

      {/* Overlay */}
      <div className="absolute inset-0 bg-black/30" />

      {/* Content */}
      <div className={`relative z-10 h-full flex flex-col md:flex-row items-center gap-6 p-6 sm:p-10 transition-opacity duration-300 ${animating ? 'opacity-0' : 'opacity-100'}`}
        style={{ minHeight: '380px' }}>

        {/* Text side */}
        <div className="flex-1 text-white text-center md:text-left">
          {cat && (
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold text-white mb-4 ${g.badge}`}>
              {cat}
            </span>
          )}
          {product.featured && (
            <span className="inline-block ml-2 px-3 py-1 rounded-full text-xs font-bold bg-orange-500 text-white mb-4">
              ★ Featured
            </span>
          )}

          <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white leading-tight mb-3 drop-shadow-sm">
            {product.name}
          </h2>

          {(product.short_description || product.description) && (
            <p className="text-white/80 text-sm sm:text-base mb-4 max-w-md line-clamp-2 mx-auto md:mx-0">
              {product.short_description || product.description}
            </p>
          )}

          <p className="text-3xl font-extrabold text-orange-300 mb-6">
            {product.currency} {isNaN(price) ? '—' : price.toFixed(2)}
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center md:justify-start">
            <button
              onClick={() => { onQuickView(product); }}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white text-purple-800 font-bold rounded-xl shadow hover:bg-purple-50 transition text-sm"
            >
              View Details
            </button>
            <button
              onClick={() => { onAddToCart(product.id); }}
              disabled={product.stock_quantity === 0 || cartLoading}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-xl shadow transition text-sm disabled:bg-gray-500 disabled:cursor-not-allowed"
            >
              <FiShoppingCart className="w-4 h-4" />
              {product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
            </button>
            {waLink && (
              <a
                href={waLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white border border-white/30 font-semibold rounded-xl transition text-sm backdrop-blur-sm"
              >
                <FiMessageCircle className="w-4 h-4" />
                Ask on WhatsApp
              </a>
            )}
          </div>
        </div>

        {/* Image side */}
        <div className="hidden md:flex flex-shrink-0 w-72 h-64 rounded-2xl overflow-hidden shadow-2xl border-2 border-white/20 items-center justify-center bg-white/10 backdrop-blur-sm">
          {product.images && product.images.length > 0 ? (
            <img
              src={product.images[0].image}
              alt={product.images[0].alt_text || product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <PlaceholderIcon category={cat} />
          )}
        </div>
      </div>

      {/* Prev / Next */}
      {slides.length > 1 && (
        <>
          <button
            onClick={() => { prev(); resetTimer(); }}
            className="absolute left-3 top-1/2 -translate-y-1/2 z-20 p-2 bg-white/20 hover:bg-white/40 backdrop-blur-sm rounded-full text-white transition shadow"
            aria-label="Previous"
          >
            <FiChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => { next(); resetTimer(); }}
            className="absolute right-3 top-1/2 -translate-y-1/2 z-20 p-2 bg-white/20 hover:bg-white/40 backdrop-blur-sm rounded-full text-white transition shadow"
            aria-label="Next"
          >
            <FiChevronRight className="w-5 h-5" />
          </button>
        </>
      )}

      {/* Dot indicators */}
      {slides.length > 1 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 flex items-center gap-1.5">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => { go(i); resetTimer(); }}
              className={`rounded-full transition-all duration-300 ${
                i === idx ? 'bg-white w-6 h-2' : 'bg-white/40 w-2 h-2 hover:bg-white/70'
              }`}
              aria-label={`Slide ${i + 1}`}
            />
          ))}
        </div>
      )}

      {/* Trust strip */}
      <div className="absolute bottom-0 left-0 right-0 z-20 bg-black/20 backdrop-blur-sm border-t border-white/10 px-6 py-2 hidden sm:flex flex-wrap gap-4 justify-center">
        {['✓ PayNow Accepted', '✓ Free Quote', '✓ WhatsApp Support', '✓ Warranty Included', '✓ Nationwide Delivery'].map((b) => (
          <span key={b} className="text-xs font-semibold text-white/80">{b}</span>
        ))}
      </div>
    </section>
  );
}
