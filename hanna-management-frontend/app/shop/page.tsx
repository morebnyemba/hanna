'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import apiClient from '@/app/lib/apiClient';
import { normalizePaginatedResponse } from '@/app/lib/apiUtils';

import ShopHeader from './_components/ShopHeader';
import HeroBanner from './_components/HeroBanner';
import CategoryPills from './_components/CategoryPills';
import ProductGrid from './_components/ProductGrid';
import ProductDetailModal from './_components/ProductDetailModal';
import CartDrawer, { type Cart, type CartItem } from './_components/CartDrawer';
import AIAssistantFAB from './_components/AIAssistantFAB';
import ShopFooter from './_components/ShopFooter';
import ToastStack, { type ToastData } from './_components/ToastStack';
import type { Product } from './_components/ProductCard';

const PRODUCTS_CACHE_KEY = 'hanna_shop_products_v1';

// ─── Types ───────────────────────────────────────────────────────────────────

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

// ─── Component ───────────────────────────────────────────────────────────────

export default function PublicShopPage() {
  // Products
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAvailableOnly, setShowAvailableOnly] = useState<boolean>(false);

  // Cart
  const [cart, setCart] = useState<Cart | null>(null);
  const [cartLoading, setCartLoading] = useState(false);
  const [showCart, setShowCart] = useState(false);
  const [clearConfirm, setClearConfirm] = useState(false);

  // Checkout
  const [checkoutStep, setCheckoutStep] = useState<number>(1);
  const [deliveryDetails, setDeliveryDetails] = useState<DeliveryDetails>({
    fullName: '', email: '', phone: '', address: '', city: '', notes: '',
  });
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof DeliveryDetails, string>>>({});
  const [paymentMethod, setPaymentMethod] = useState<'ecocash' | 'omari' | 'innbucks' | 'telecash'>('ecocash');
  const [paymentInfo, setPaymentInfo] = useState<PaymentInfo | null>(null);
  const [otpCode, setOtpCode] = useState('');

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

  // ── Debounce search ─────────────────────────────────────────────────────────
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState('');
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => setDebouncedSearch(searchQuery), 150);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [searchQuery]);

  // ── CSRF + initial load ─────────────────────────────────────────────────────
  useEffect(() => {
    // Instant paint from session cache while fresh data loads in background
    try {
      const cached = sessionStorage.getItem(PRODUCTS_CACHE_KEY);
      if (cached) {
        const parsed: Product[] = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          setProducts(parsed);
          setLoading(false);
        }
      }
    } catch {
      // Cache read is best-effort
    }

    // CSRF, products and cart all load in parallel — none blocks another
    apiClient.get('/crm-api/products/csrf/')
      .then((res) => { if (res.data?.token) setCsrfToken(res.data.token); })
      .catch(() => {});
    fetchProducts();
    fetchCart();
  }, []);

  // ── Data fetching ────────────────────────────────────────────────────────────
  const fetchProducts = async () => {
    try {
      let all: Product[] = [];
      let next: string | null = '/crm-api/products/products/';
      let firstPage = true;
      while (next) {
        const res: any = await apiClient.get(next);
        all = [...all, ...normalizePaginatedResponse<Product>(res.data)];
        next = res.data.next ? res.data.next.replace(/^https?:\/\/[^/]+/, '') : null;
        // Paint the first page immediately; remaining pages stream in behind it
        const active = all.filter((p) => p.is_active);
        setProducts(active);
        if (firstPage) {
          setLoading(false);
          firstPage = false;
        }
      }
      try {
        sessionStorage.setItem(PRODUCTS_CACHE_KEY, JSON.stringify(all.filter((p) => p.is_active)));
      } catch {
        // Cache write is best-effort
      }
    } catch {
      // Only surface an error if we have nothing to show (no cache hit)
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
    } catch {
      // Cart fetch failure is non-fatal
    }
  };

  const csrfHeaders = useCallback(() => (
    csrfToken ? { headers: { 'X-CSRFToken': csrfToken } } : {}
  ), [csrfToken]);

  // ── Cart operations ──────────────────────────────────────────────────────────
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

  // ── Checkout ─────────────────────────────────────────────────────────────────
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

  const proceedToNextStep = () => {
    if (checkoutStep === 1) {
      setCheckoutStep(2);
    } else if (checkoutStep === 2) {
      if (validateDelivery()) setCheckoutStep(3);
    }
  };

  const placeOrder = async () => {
    setCartLoading(true);
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
        poll_url: d.poll_url,
        payment_method: d.payment_method || paymentMethod,
        requires_otp: d.requires_otp || false,
        otp_message: d.otp_message,
        authorization_code: d.authorization_code,
        authorization_expires: d.authorization_expires,
        deeplink: d.deeplink,
        redirect_url: d.redirect_url,
      });
      setCheckoutStep(4);
    } catch (err: any) {
      pushToast(err?.response?.data?.message || err?.message || 'Failed to place order', 'error');
    } finally {
      setCartLoading(false);
    }
  };

  const submitOTP = async () => {
    if (!otpCode || !paymentInfo?.paynow_reference) {
      pushToast('Please enter the OTP code', 'error');
      return;
    }
    setCartLoading(true);
    try {
      const res = await apiClient.post('/crm-api/paynow/submit-otp/', {
        payment_reference: paymentInfo.paynow_reference,
        otp_code: otpCode,
      }, csrfHeaders());
      if (res.data?.success) {
        setOtpCode('');
        setCheckoutStep(5);
      } else {
        pushToast(res.data?.message || 'Failed to submit OTP', 'error');
      }
    } catch (err: any) {
      pushToast(err?.response?.data?.message || 'Failed to submit OTP', 'error');
    } finally {
      setCartLoading(false);
    }
  };

  const handleDone = () => {
    setShowCart(false);
    setCheckoutStep(1);
    setPaymentInfo(null);
    setOtpCode('');
    setDeliveryDetails({ fullName: '', email: '', phone: '', address: '', city: '', notes: '' });
    setFieldErrors({});
    fetchCart();
  };

  // ── Derived data ─────────────────────────────────────────────────────────────
  const allCategories = Array.from(
    new Set(products.map((p) => p.category?.name).filter((n): n is string => Boolean(n)))
  );
  const categories = ['all', ...allCategories];

  const filteredProducts = products.filter((p) => {
    if (selectedCategory !== 'all' && p.category?.name !== selectedCategory) return false;
    if (showAvailableOnly && p.stock_quantity === 0) return false;
    if (debouncedSearch.trim()) {
      const q = debouncedSearch.toLowerCase();
      return p.name.toLowerCase().includes(q) || (p.description || '').toLowerCase().includes(q);
    }
    return true;
  });

  const productCounts: Record<string, number> = {
    all: products.length,
    ...Object.fromEntries(
      allCategories.map((cat) => [cat, products.filter((p) => p.category?.name === cat).length])
    ),
  };

  const cartItemCount = cart?.total_items ?? 0;

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-white">
      <ShopHeader
        cartItemCount={cartItemCount}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onCartOpen={() => { setShowCart(true); }}
        onAssistantToggle={() => setShowAssistant((v) => !v)}
        showMobileMenu={showMobileMenu}
        onMobileMenuToggle={() => setShowMobileMenu((v) => !v)}
        showAssistant={showAssistant}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <HeroBanner
          whatsappNumber={whatsappNumber}
          onShopNow={() => {
            document.getElementById('product-section')?.scrollIntoView({ behavior: 'smooth' });
          }}
        />

        <div id="product-section">
          <CategoryPills
            categories={categories}
            selected={selectedCategory}
            onSelect={setSelectedCategory}
            productCounts={productCounts}
            showAvailableOnly={showAvailableOnly}
            onAvailableToggle={setShowAvailableOnly}
          />

          <ProductGrid
            products={filteredProducts}
            loading={loading}
            error={error}
            selectedCategory={selectedCategory}
            onAddToCart={addToCart}
            onQuickView={setQuickViewProduct}
            cartLoading={cartLoading}
          />
        </div>
      </main>

      <ShopFooter whatsappNumber={whatsappNumber} />

      {/* Product detail modal */}
      <ProductDetailModal
        product={quickViewProduct}
        whatsappNumber={whatsappNumber}
        onClose={() => setQuickViewProduct(null)}
        onAddToCart={addToCart}
        cartLoading={cartLoading}
      />

      {/* Cart + Checkout drawer */}
      <CartDrawer
        open={showCart}
        cart={cart}
        cartLoading={cartLoading}
        checkoutStep={checkoutStep}
        deliveryDetails={deliveryDetails}
        paymentMethod={paymentMethod}
        paymentInfo={paymentInfo}
        otpCode={otpCode}
        fieldErrors={fieldErrors}
        clearConfirm={clearConfirm}
        onClose={() => { setShowCart(false); setCheckoutStep(1); }}
        onUpdateQty={updateCartItem}
        onRemove={removeFromCart}
        onClearRequest={() => setClearConfirm(true)}
        onClearConfirm={clearCart}
        onClearCancel={() => setClearConfirm(false)}
        onDeliveryChange={(e) => {
          const { name, value } = e.target;
          setDeliveryDetails((prev) => ({ ...prev, [name]: value }));
          if (fieldErrors[name as keyof DeliveryDetails]) {
            setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
          }
        }}
        onPaymentMethodChange={setPaymentMethod}
        onProceed={proceedToNextStep}
        onBack={() => setCheckoutStep((s) => Math.max(1, s - 1))}
        onPlaceOrder={placeOrder}
        onOtpChange={setOtpCode}
        onSubmitOTP={submitOTP}
        onDone={handleDone}
      />

      {/* Floating AI Assistant */}
      <AIAssistantFAB
        whatsappNumber={whatsappNumber}
        open={showAssistant}
        onToggle={() => setShowAssistant((v) => !v)}
      />

      {/* Toast notifications */}
      <ToastStack toasts={toasts} onDismiss={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))} />
    </div>
  );
}
