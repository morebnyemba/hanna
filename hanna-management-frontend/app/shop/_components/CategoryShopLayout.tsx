'use client';

import { useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { FiSearch, FiX, FiArrowLeft, FiFilter, FiShoppingCart } from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';
import { normalizePaginatedResponse } from '@/app/lib/apiUtils';

import ShopHeader from './ShopHeader';
import ProductGrid from './ProductGrid';
import ProductDetailModal from './ProductDetailModal';
import CartDrawer, { type Cart } from './CartDrawer';
import AIAssistantFAB from './AIAssistantFAB';
import ShopFooter from './ShopFooter';
import ToastStack, { type ToastData } from './ToastStack';
import type { Product } from './ProductCard';

const PRODUCTS_CACHE_KEY = 'hanna_shop_products_v1';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface CategoryConfig {
  title: string;
  subtitle: string;
  description: string;
  /** Lower-case terms — product matches if name/description/category includes ANY of them */
  searchTerms: string[];
  theme: {
    gradient: string;
    badge: string;
    accent: string;
    ring: string;
    light: string;
  };
  icon: ReactNode;
  breadcrumb: { label: string; href: string }[];
}

// ─── Category Hero ────────────────────────────────────────────────────────────

function CategoryHero({
  config,
  productCount,
  whatsappNumber,
}: {
  config: CategoryConfig;
  productCount: number;
  whatsappNumber: string;
}) {
  const waLink = whatsappNumber
    ? `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(`Hi, I'd like a quote on ${config.title}`)}`
    : null;

  return (
    <section className={`relative overflow-hidden rounded-2xl mb-8 bg-gradient-to-br ${config.theme.gradient} shadow-lg`}>
      {/* Decorative circles */}
      <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full bg-white/10 pointer-events-none" />
      <div className="absolute bottom-0 left-8 w-32 h-32 rounded-full bg-white/5 pointer-events-none" />

      <div className="relative px-6 sm:px-10 py-10 sm:py-14 flex flex-col md:flex-row items-center gap-8">
        {/* Icon */}
        <div className={`flex-shrink-0 w-24 h-24 rounded-3xl bg-white/20 backdrop-blur-sm flex items-center justify-center shadow-lg border border-white/30`}>
          <span className="text-white [&>svg]:w-12 [&>svg]:h-12">{config.icon}</span>
        </div>

        {/* Text */}
        <div className="flex-1 text-white text-center md:text-left">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-1.5 text-xs text-white/60 mb-3 justify-center md:justify-start flex-wrap">
            {config.breadcrumb.map((crumb, i) => (
              <span key={crumb.href} className="flex items-center gap-1.5">
                {i > 0 && <span>/</span>}
                <Link href={crumb.href} className="hover:text-white transition">{crumb.label}</Link>
              </span>
            ))}
            <span>/</span>
            <span className="text-white font-semibold">{config.title}</span>
          </nav>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-white leading-tight mb-2 drop-shadow-sm">
            {config.title}
          </h1>
          <p className="text-white/80 text-base mb-4 max-w-lg mx-auto md:mx-0">
            {config.description}
          </p>

          <div className="flex flex-wrap items-center gap-3 justify-center md:justify-start">
            <span className={`${config.theme.badge} text-white text-sm font-bold px-4 py-1.5 rounded-full shadow`}>
              {productCount} Product{productCount !== 1 ? 's' : ''} Available
            </span>
            {waLink && (
              <a
                href={waLink}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm font-semibold text-white/90 hover:text-white border border-white/30 hover:border-white/60 px-4 py-1.5 rounded-full transition"
              >
                💬 Get a Free Quote
              </a>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

// ─── Main Layout ──────────────────────────────────────────────────────────────

interface CategoryShopLayoutProps {
  config: CategoryConfig;
}

export default function CategoryShopLayout({ config }: CategoryShopLayoutProps) {
  const router = useRouter();

  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Secondary search within the category
  const [searchQuery, setSearchQuery] = useState('');
  const [showAvailableOnly, setShowAvailableOnly] = useState(false);

  const [cart, setCart] = useState<Cart | null>(null);
  const [cartLoading, setCartLoading] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [clearConfirm, setClearConfirm] = useState(false);

  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showAssistant, setShowAssistant] = useState(false);
  const [quickViewProduct, setQuickViewProduct] = useState<Product | null>(null);

  const [csrfToken, setCsrfToken] = useState<string | null>(null);

  const [toasts, setToasts] = useState<ToastData[]>([]);
  const toastId = useRef(0);
  const pushToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    const id = ++toastId.current;
    setToasts((prev) => [...prev.slice(-2), { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
  }, []);

  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '';

  // Debounced search
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(searchQuery), 150);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [searchQuery]);

  useEffect(() => {
    // Warm from shared session cache
    try {
      const cached = sessionStorage.getItem(PRODUCTS_CACHE_KEY);
      if (cached) {
        const parsed: Product[] = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setAllProducts(parsed);
          setLoading(false);
        }
      }
    } catch { /* best-effort */ }

    apiClient.get('/crm-api/products/csrf/')
      .then((res) => { if (res.data?.token) setCsrfToken(res.data.token); })
      .catch(() => {});
    fetchProducts();
    fetchCart();
  }, []);

  const fetchProducts = async () => {
    try {
      let all: Product[] = [];
      let next: string | null = '/crm-api/products/products/';
      let firstPage = true;
      while (next) {
        const res: any = await apiClient.get(next);
        all = [...all, ...normalizePaginatedResponse<Product>(res.data)];
        next = res.data.next ? res.data.next.replace(/^https?:\/\/[^/]+/, '') : null;
        setAllProducts(all.filter((p) => p.is_active));
        if (firstPage) { setLoading(false); firstPage = false; }
      }
      try {
        sessionStorage.setItem(PRODUCTS_CACHE_KEY, JSON.stringify(all.filter((p) => p.is_active)));
      } catch { /* best-effort */ }
    } catch {
      setAllProducts((prev) => {
        if (prev.length === 0) setError('Failed to load products.');
        return prev;
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCart = async () => {
    try {
      const res = await apiClient.get('/crm-api/products/cart/');
      setCart(res.data);
    } catch { /* non-fatal */ }
  };

  const csrfHeaders = useCallback(() => (
    csrfToken ? { headers: { 'X-CSRFToken': csrfToken } } : {}
  ), [csrfToken]);

  const addToCart = async (productId: number, quantity = 1) => {
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/products/cart/add/', { product_id: productId, quantity }, csrfHeaders());
      setCart(res.data.cart);
      const name = allProducts.find((p) => p.id === productId)?.name || 'Item';
      pushToast(`${name} added to cart`);
    } catch (err: any) {
      const msg = err?.response?.data?.error;
      pushToast(typeof msg === 'string' ? msg : msg?.detail || 'Failed to add item to cart', 'error');
    } finally {
      setCartLoading(false);
    }
  };

  const updateCartItem = async (cartItemId: number, quantity: number) => {
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/products/cart/update/', { cart_item_id: cartItemId, quantity }, csrfHeaders());
      setCart(res.data.cart);
    } catch (err: any) {
      pushToast(err?.response?.data?.error || 'Failed to update cart', 'error');
    } finally { setCartLoading(false); }
  };

  const removeFromCart = async (cartItemId: number) => {
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/products/cart/remove/', { cart_item_id: cartItemId }, csrfHeaders());
      setCart(res.data.cart);
    } catch (err: any) {
      pushToast(err?.response?.data?.error || 'Failed to remove item', 'error');
    } finally { setCartLoading(false); }
  };

  const clearCart = async () => {
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/products/cart/clear/', {}, csrfHeaders());
      setCart(res.data.cart);
      setClearConfirm(false);
      pushToast('Cart cleared');
    } catch (err: any) {
      pushToast(err?.response?.data?.error || 'Failed to clear cart', 'error');
    } finally { setCartLoading(false); }
  };

  // Filter: first apply category terms, then user's secondary search
  const categoryProducts = allProducts.filter((p) => {
    const haystack = `${p.name} ${p.description || ''} ${p.category?.name || ''}`.toLowerCase();
    return config.searchTerms.some((t) => haystack.includes(t.toLowerCase()));
  });

  const filteredProducts = categoryProducts.filter((p) => {
    if (showAvailableOnly && p.stock_quantity === 0) return false;
    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase();
      return p.name.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q);
    }
    return true;
  });

  const cartItemCount = cart?.total_items ?? 0;

  return (
    <div className="min-h-screen bg-white">
      <ShopHeader
        cartItemCount={cartItemCount}
        searchQuery=""
        onSearchChange={() => {}}
        onCartOpen={() => setShowCart(true)}
        onAssistantToggle={() => setShowAssistant((v) => !v)}
        showMobileMenu={showMobileMenu}
        onMobileMenuToggle={() => setShowMobileMenu((v) => !v)}
        showAssistant={showAssistant}
        onNavFilter={() => {}}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <CategoryHero
          config={config}
          productCount={filteredProducts.length}
          whatsappNumber={whatsappNumber}
        />

        {/* Secondary search + filters */}
        <div className={`flex flex-col sm:flex-row gap-3 items-center mb-6 p-4 bg-white rounded-2xl border ${config.theme.ring} shadow-sm`}>
          <div className="relative flex-1 w-full">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none" />
            <input
              type="text"
              placeholder={`Search within ${config.title}…`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`w-full pl-9 pr-9 py-2.5 rounded-xl border text-sm focus:outline-none focus:ring-2 ${config.theme.ring} transition bg-gray-50 hover:bg-white`}
            />
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
                <FiX className="w-4 h-4" />
              </button>
            )}
          </div>

          <label className={`flex items-center gap-2 text-sm font-semibold cursor-pointer flex-shrink-0 px-4 py-2.5 rounded-xl border transition ${
            showAvailableOnly ? `${config.theme.light} ${config.theme.accent} ${config.theme.ring}` : 'border-gray-200 text-gray-600 hover:bg-gray-50'
          }`}>
            <input
              type="checkbox"
              checked={showAvailableOnly}
              onChange={(e) => setShowAvailableOnly(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <FiFilter className="w-3.5 h-3.5" />
            In Stock Only
          </label>

          <Link
            href="/shop"
            className="flex items-center gap-1.5 text-sm font-semibold text-gray-500 hover:text-purple-700 transition flex-shrink-0"
          >
            <FiArrowLeft className="w-4 h-4" />
            All Products
          </Link>
        </div>

        <ProductGrid
          products={filteredProducts}
          loading={loading}
          error={error}
          selectedCategory="all"
          onAddToCart={addToCart}
          onQuickView={setQuickViewProduct}
          cartLoading={cartLoading}
        />

        {/* Empty state specific to category */}
        {!loading && filteredProducts.length === 0 && !error && (
          <div className="text-center py-16">
            <div className={`w-20 h-20 rounded-full ${config.theme.light} flex items-center justify-center mx-auto mb-4`}>
              <span className={`${config.theme.accent} [&>svg]:w-10 [&>svg]:h-10`}>{config.icon}</span>
            </div>
            <h3 className="text-lg font-extrabold text-purple-900 mb-2">No {config.title} Found</h3>
            <p className="text-gray-500 text-sm mb-4">
              {searchQuery ? `No results for "${searchQuery}" in ${config.title}.` : `We're adding more ${config.title} soon!`}
            </p>
            {searchQuery && (
              <button onClick={() => setSearchQuery('')} className="text-purple-600 font-semibold hover:underline text-sm">
                Clear search
              </button>
            )}
          </div>
        )}
      </main>

      <ShopFooter whatsappNumber={whatsappNumber} />

      <ProductDetailModal
        product={quickViewProduct}
        whatsappNumber={whatsappNumber}
        onClose={() => setQuickViewProduct(null)}
        onAddToCart={addToCart}
        cartLoading={cartLoading}
      />

      <CartDrawer
        open={showCart}
        cart={cart}
        cartLoading={cartLoading}
        clearConfirm={clearConfirm}
        onClose={() => setShowCart(false)}
        onUpdateQty={updateCartItem}
        onRemove={removeFromCart}
        onClearRequest={() => setClearConfirm(true)}
        onClearConfirm={clearCart}
        onClearCancel={() => setClearConfirm(false)}
        onCheckout={() => { setShowCart(false); router.push('/shop/checkout'); }}
      />

      <AIAssistantFAB
        whatsappNumber={whatsappNumber}
        open={showAssistant}
        onToggle={() => setShowAssistant((v) => !v)}
      />

      <ToastStack toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
}
