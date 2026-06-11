'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  FiChevronLeft, FiChevronRight, FiShoppingCart,
  FiMessageCircle, FiEye,
} from 'react-icons/fi';
import type { Product } from './ProductCard';

// ─── Unsplash fallback images keyed by product_type + category keyword ────────

const UNSPLASH = {
  solar:     'https://images.unsplash.com/photo-1509391366360-2e959784a276?w=1400&q=85&fit=crop',
  starlink:  'https://images.unsplash.com/photo-1614730321146-b6fa6a46bcb4?w=1400&q=85&fit=crop',
  furniture: 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=1400&q=85&fit=crop',
  bedroom:   'https://images.unsplash.com/photo-1540518614846-7eded433c457?w=1400&q=85&fit=crop',
  kitchen:   'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1400&q=85&fit=crop',
  hardware:  'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1400&q=85&fit=crop',
  service:   'https://images.unsplash.com/photo-1600880292203-757bb62b4baf?w=1400&q=85&fit=crop',
  software:  'https://images.unsplash.com/photo-1555949963-aa79dcee981c?w=1400&q=85&fit=crop',
  module:    'https://images.unsplash.com/photo-1518770660439-4636190af475?w=1400&q=85&fit=crop',
  default:   'https://images.unsplash.com/photo-1607082348824-0a96f2a4b9da?w=1400&q=85&fit=crop',
} as const;

function fallbackImage(product: Product): string {
  const cat = (product.category?.name || '').toLowerCase();
  const type = (product.product_type || '').toLowerCase();
  if (cat.includes('solar') || cat.includes('panel') || cat.includes('battery')) return UNSPLASH.solar;
  if (cat.includes('starlink') || cat.includes('wifi') || cat.includes('internet')) return UNSPLASH.starlink;
  if (cat.includes('bedroom')) return UNSPLASH.bedroom;
  if (cat.includes('kitchen')) return UNSPLASH.kitchen;
  if (cat.includes('furniture') || cat.includes('fitted') || cat.includes('luxury')) return UNSPLASH.furniture;
  if (type === 'service') return UNSPLASH.service;
  if (type === 'software') return UNSPLASH.software;
  if (type === 'module') return UNSPLASH.module;
  if (type === 'hardware') return UNSPLASH.hardware;
  return UNSPLASH.default;
}

function slideTheme(product: Product) {
  const cat = (product.category?.name || '').toLowerCase();
  const type = (product.product_type || '').toLowerCase();
  if (cat.includes('solar') || cat.includes('panel') || cat.includes('battery'))
    return { gradient: 'from-orange-600/80 via-amber-600/60 to-transparent', badge: 'bg-orange-500', price: 'text-amber-200' };
  if (cat.includes('starlink') || cat.includes('wifi'))
    return { gradient: 'from-sky-700/85 via-blue-600/60 to-transparent', badge: 'bg-sky-500', price: 'text-sky-200' };
  if (cat.includes('furniture') || cat.includes('bedroom') || cat.includes('kitchen') || cat.includes('luxury') || cat.includes('fitted'))
    return { gradient: 'from-slate-800/85 via-slate-700/60 to-transparent', badge: 'bg-indigo-500', price: 'text-indigo-200' };
  if (type === 'service')
    return { gradient: 'from-sky-800/85 via-sky-600/60 to-transparent', badge: 'bg-sky-600', price: 'text-sky-200' };
  return { gradient: 'from-sky-800/85 via-blue-700/60 to-transparent', badge: 'bg-sky-600', price: 'text-sky-100' };
}

interface HeroCarouselProps {
  products: Product[];
  whatsappNumber: string;
  onAddToCart: (id: number) => void;
  onQuickView: (product: Product) => void;
  cartLoading: boolean;
}

export default function HeroCarousel({ products, whatsappNumber, onAddToCart, onQuickView, cartLoading }: HeroCarouselProps) {
  const [idx, setIdx] = useState(0);
  const [fade, setFade] = useState(true);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Prefer featured products first, cap at 8
  const slides = [
    ...products.filter((p) => p.is_active && p.featured),
    ...products.filter((p) => p.is_active && !p.featured),
  ].slice(0, 8);

  const go = useCallback((next: number) => {
    setFade(false);
    setTimeout(() => { setIdx(next); setFade(true); }, 250);
  }, []);

  const prev = useCallback(() => go((idx - 1 + slides.length) % slides.length), [go, idx, slides.length]);
  const next = useCallback(() => go((idx + 1) % slides.length), [go, idx, slides.length]);

  const resetTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (slides.length > 1) timerRef.current = setInterval(next, 5500);
  }, [next, slides.length]);

  useEffect(() => {
    resetTimer();
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [resetTimer]);

  if (slides.length === 0) return null;

  const product = slides[idx];
  const imgSrc = product.images && product.images.length > 0
    ? product.images[0].image
    : fallbackImage(product);
  const theme = slideTheme(product);
  const price = parseFloat(product.price);
  const waLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(`Hi, I'm interested in: ${product.name}`)}`
    : null;

  return (
    <section className="relative mb-8 rounded-2xl overflow-hidden shadow-xl" style={{ height: '460px' }}>
      {/* Full-bleed background image */}
      <div
        className={`absolute inset-0 transition-opacity duration-500 ${fade ? 'opacity-100' : 'opacity-0'}`}
        style={{
          backgroundImage: `url(${imgSrc})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      />

      {/* Left-to-right gradient overlay so text is readable */}
      <div className={`absolute inset-0 bg-gradient-to-r ${theme.gradient} to-black/10`} />
      {/* Bottom fade for trust strip */}
      <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/50 to-transparent" />

      {/* Content */}
      <div
        className={`relative z-10 h-full flex flex-col justify-center px-8 sm:px-14 max-w-2xl transition-all duration-500 ${fade ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'}`}
      >
        <div className="flex items-center gap-2 mb-4 flex-wrap">
          {product.category && (
            <span className={`text-xs font-bold px-3 py-1 rounded-full text-white ${theme.badge}`}>
              {product.category.name}
            </span>
          )}
          {product.featured && (
            <span className="text-xs font-bold px-3 py-1 rounded-full bg-orange-500 text-white">
              ★ Featured
            </span>
          )}
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-white/20 text-white backdrop-blur-sm capitalize">
            {product.product_type}
          </span>
        </div>

        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white leading-tight mb-3 drop-shadow-lg">
          {product.name}
        </h2>

        {(product.short_description || product.description) && (
          <p className="text-white/85 text-sm sm:text-base mb-5 max-w-lg line-clamp-2 leading-relaxed">
            {product.short_description || product.description}
          </p>
        )}

        <p className={`text-4xl font-extrabold mb-6 drop-shadow ${theme.price}`}>
          {product.currency} {isNaN(price) ? '—' : price.toFixed(2)}
        </p>

        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => onQuickView(product)}
            className="inline-flex items-center gap-2 px-6 py-3 bg-white text-sky-800 font-bold rounded-xl shadow-lg hover:bg-sky-50 transition text-sm"
          >
            <FiEye className="w-4 h-4" />
            View Details
          </button>
          <button
            onClick={() => onAddToCart(product.id)}
            disabled={product.stock_quantity === 0 || cartLoading}
            className="inline-flex items-center gap-2 px-6 py-3 bg-orange-500 hover:bg-orange-600 text-white font-bold rounded-xl shadow-lg transition text-sm disabled:bg-gray-500 disabled:cursor-not-allowed"
          >
            <FiShoppingCart className="w-4 h-4" />
            {product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
          </button>
          {waLink && (
            <a
              href={waLink}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 bg-white/15 hover:bg-white/25 text-white border border-white/40 font-semibold rounded-xl transition text-sm backdrop-blur-sm"
            >
              <FiMessageCircle className="w-4 h-4" />
              WhatsApp
            </a>
          )}
        </div>
      </div>

      {/* Prev / Next */}
      {slides.length > 1 && (
        <>
          <button
            onClick={() => { prev(); resetTimer(); }}
            className="absolute left-4 top-1/2 -translate-y-1/2 z-20 p-2.5 bg-white/20 hover:bg-white/40 backdrop-blur-sm rounded-full text-white transition shadow-lg"
            aria-label="Previous"
          >
            <FiChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={() => { next(); resetTimer(); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 z-20 p-2.5 bg-white/20 hover:bg-white/40 backdrop-blur-sm rounded-full text-white transition shadow-lg"
            aria-label="Next"
          >
            <FiChevronRight className="w-5 h-5" />
          </button>
        </>
      )}

      {/* Dots */}
      {slides.length > 1 && (
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2">
          {slides.map((_, i) => (
            <button
              key={i}
              onClick={() => { go(i); resetTimer(); }}
              className={`rounded-full transition-all duration-300 shadow ${
                i === idx ? 'bg-white w-7 h-2.5' : 'bg-white/40 w-2.5 h-2.5 hover:bg-white/70'
              }`}
              aria-label={`Slide ${i + 1}`}
            />
          ))}
        </div>
      )}

      {/* Trust strip */}
      <div className="absolute bottom-0 inset-x-0 z-20 px-6 py-2.5 flex flex-wrap gap-5 justify-center sm:justify-start">
        {['✓ PayNow Accepted', '✓ Free Quote', '✓ WhatsApp Support', '✓ Warranty Included', '✓ Nationwide Delivery'].map((b) => (
          <span key={b} className="text-xs font-semibold text-white/80 tracking-wide">{b}</span>
        ))}
      </div>
    </section>
  );
}
