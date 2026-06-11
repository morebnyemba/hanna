'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/app/lib/apiClient';
import { normalizePaginatedResponse } from '@/app/lib/apiUtils';

import ShopHeader from './_components/ShopHeader';
import HeroCarousel from './_components/HeroCarousel';
import CategoryPills, { type ProductTypeFilter } from './_components/CategoryPills';
import ProductGrid from './_components/ProductGrid';
import ProductDetailModal from './_components/ProductDetailModal';
import CartDrawer, { type Cart } from './_components/CartDrawer';
import AIAssistantFAB from './_components/AIAssistantFAB';
import ShopFooter from './_components/ShopFooter';
import ToastStack, { type ToastData } from './_components/ToastStack';
import type { Product } from './_components/ProductCard';

const PRODUCTS_CACHE_KEY = 'hanna_shop_products_v1';

export default function PublicShopPage() {
  const router = useRouter();

  // Products
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedType, setSelectedType] = useState<ProductTypeFilter>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAvailableOnly, setShowAvailableOnly] = useState<boolean>(false);

  // Cart
  const [cart, setCart] = useState<Cart | null>(null);
  const [cartLoading, setCartLoading] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [clearConfirm, setClearConfirm] = useState(false);

  // UI
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const [showAssistant, setShowAssistant] = useState(false);
  const [quickViewProduct, setQuickViewProduct] = useState<Product | null>(null);

  // CSRF
  const [csrfToken, setCsrfToken] = useState<string | null>(null);

  // Toasts
  const [toasts, setToasts] = useState<ToastData[]>([]);
  const toastId = useRef(0);
  const pushToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    const id = ++toastId.current;
    setToasts((prev) => [...prev.slice(-2), { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 3000);
  }, []);

  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '';

  // Debounce search
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(searchQuery), 150);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [searchQuery]);

  // Initial load
  useEffect(() => {
    try {
      const cached = sessionStorage.getItem(PRODUCTS_CACHE_KEY);
      if (cached) {
        const parsed: Product[] = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setProducts(parsed);
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
        const active = all.filter((p) => p.is_active);
        setProducts(active);
        if (firstPage) { setLoading(false); firstPage = false; }
      }
      try {
        sessionStorage.setItem(PRODUCTS_CACHE_KEY, JSON.stringify(all.filter((p) => p.is_active)));
      } catch { /* best-effort */ }
    } catch {
      setProducts((prev) => {
        if (prev.length === 0) setError('Failed to load products. Please try again later.');
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

  // Cart operations
  const addToCart = async (productId: number, quantity = 1) => {
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/products/cart/add/', { product_id: productId, quantity }, csrfHeaders());
      setCart(res.data.cart);
      const name = products.find((p) => p.id === productId)?.name || 'Item';
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
    } finally {
      setCartLoading(false);
    }
  };

  const removeFromCart = async (cartItemId: number) => {
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/products/cart/remove/', { cart_item_id: cartItemId }, csrfHeaders());
      setCart(res.data.cart);
    } catch (err: any) {
      pushToast(err?.response?.data?.error || 'Failed to remove item', 'error');
    } finally {
      setCartLoading(false);
    }
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
    } finally {
      setCartLoading(false);
    }
  };

  // Derived data — filter by product_type
  const filteredProducts = products.filter((p) => {
    if (selectedType !== 'all' && p.product_type !== selectedType) return false;
    if (showAvailableOnly && p.stock_quantity === 0) return false;
    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase();
      return (
        p.name.toLowerCase().includes(q) ||
        (p.description || '').toLowerCase().includes(q) ||
        (p.category?.name || '').toLowerCase().includes(q)
      );
    }
    return true;
  });

  // Counts per type for pill badges
  const typeCounts: Record<string, number> = {
    hardware: products.filter((p) => p.product_type === 'hardware').length,
    service:  products.filter((p) => p.product_type === 'service').length,
    software: products.filter((p) => p.product_type === 'software').length,
    module:   products.filter((p) => p.product_type === 'module').length,
  };

  const cartItemCount = cart?.total_items ?? 0;

  return (
    <div className="min-h-screen bg-white">
      <ShopHeader
        cartItemCount={cartItemCount}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onCartOpen={() => setShowCart(true)}
        onAssistantToggle={() => setShowAssistant((v) => !v)}
        showMobileMenu={showMobileMenu}
        onMobileMenuToggle={() => setShowMobileMenu((v) => !v)}
        showAssistant={showAssistant}
        onNavFilter={({ search }) => {
          setSearchQuery(search ?? '');
        }}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <HeroCarousel
          products={products}
          whatsappNumber={whatsappNumber}
          onAddToCart={addToCart}
          onQuickView={setQuickViewProduct}
          cartLoading={cartLoading}
        />

        <div id="product-section">
          <CategoryPills
            selected={selectedType}
            onSelect={setSelectedType}
            typeCounts={typeCounts}
            showAvailableOnly={showAvailableOnly}
            onAvailableToggle={setShowAvailableOnly}
          />

          <ProductGrid
            products={filteredProducts}
            loading={loading}
            error={error}
            selectedCategory={selectedType}
            onAddToCart={addToCart}
            onQuickView={setQuickViewProduct}
            cartLoading={cartLoading}
          />
        </div>
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
