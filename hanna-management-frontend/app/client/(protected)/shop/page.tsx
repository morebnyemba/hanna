'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { FiShoppingCart, FiPlus, FiMinus, FiTrash2, FiPackage, FiHome, FiX, FiMessageCircle, FiZap, FiCopy, FiExternalLink } from 'react-icons/fi';
import apiClient from '@/app/lib/apiClient';
import { normalizePaginatedResponse } from '@/app/lib/apiUtils';

interface Product {
  id: number;
  name: string;
  description: string;
  price: string;
  currency: string;
  is_active: boolean;
  stock_quantity: number;
  product_type: string;
  category: {
    id: number;
    name: string;
  } | null;
  images?: Array<{
    id: number;
    image: string;
    alt_text?: string;
  }>;
}

interface CartItem {
  id: number;
  product: Product;
  quantity: number;
  subtotal: string;
}

interface Cart {
  id: number;
  items: CartItem[];
  total_items: number;
  total_price: string;
}


export default function ShopPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [cartLoading, setCartLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCart, setShowCart] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAvailableOnly, setShowAvailableOnly] = useState<boolean>(false);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [showAssistant, setShowAssistant] = useState<boolean>(false);
  const [assistantPrompt, setAssistantPrompt] = useState<string>('Hi, I need help choosing a solar system for my home (2 fridges, 4 TVs, 6 lights, 2 laptops). Please suggest a reliable bundle with pricing.');
  const [assistantCopyStatus, setAssistantCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const assistantRef = useRef<HTMLDivElement | null>(null);
  const whatsappNumber = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER || '';
  const assistantQuickPrompts = [
    { label: 'Size my system', prompt: 'I need solar sizing help for a 3-bedroom home with 2 fridges, 3 TVs, lights, and phone charging. Share a safe starter bundle.' },
    { label: 'Backup for business', prompt: 'Recommend a backup solar kit for a small shop with POS, lights, laptops, and a display fridge. Budget-conscious.' },
    { label: 'Off-grid package', prompt: 'I want a fully off-grid package for a rural site. Include panels, batteries, inverter, and installation estimate.' },
    { label: 'Best value bundle', prompt: 'Show me the best-value solar bundle with good warranty and components you recommend.' },
  ];

  const buildAssistantLink = (prompt: string) => {
    if (!whatsappNumber) return null;
    return `https://wa.me/${whatsappNumber}?text=${encodeURIComponent(prompt)}`;
  };

  const copyAssistantPrompt = async (prompt: string) => {
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(prompt);
        setAssistantCopyStatus('copied');
        setTimeout(() => setAssistantCopyStatus('idle'), 2000);
      } else {
        setAssistantCopyStatus('error');
      }
    } catch (e) {
      console.error('Failed to copy prompt', e);
      setAssistantCopyStatus('error');
    }
  };

  const launchAssistant = (prompt: string) => {
    setAssistantPrompt(prompt);
    const link = buildAssistantLink(prompt);
    if (link) {
      window.open(link, '_blank', 'noopener,noreferrer');
      return;
    }
    copyAssistantPrompt(prompt);
  };

  // Close assistant on Esc key
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setShowAssistant(false);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  // Outside click to close assistant
  useEffect(() => {
    const onMouseDown = (e: MouseEvent) => {
      if (!showAssistant) return;
      const node = assistantRef.current;
      if (node && !node.contains(e.target as Node)) setShowAssistant(false);
    };
    document.addEventListener('mousedown', onMouseDown);
    return () => document.removeEventListener('mousedown', onMouseDown);
  }, [showAssistant]);
  // Fetch products
  // Fetch products (handles pagination)
  const fetchProducts = async () => {
    try {
      let allProducts: Product[] = [];
      let nextUrl: string | null = '/crm-api/products/products/';
      
      // Fetch all pages
      while (nextUrl) {
        const response: any = await apiClient.get(nextUrl);
        const pageProducts = normalizePaginatedResponse<Product>(response.data);
        allProducts = [...allProducts, ...pageProducts];
        nextUrl = response.data.next ? response.data.next.replace(/^https?:\/\/[^\/]+/, '') : null;
      }
      
      console.log('Total products fetched:', allProducts.length);
      const activeProducts = allProducts.filter((p: Product) => p.is_active);
      console.log('Active products:', activeProducts.length);
      setProducts(activeProducts);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching products:', err);
      setError('Failed to load products. Please try again later.');
      setLoading(false);
    }
  };

  // Fetch cart
  const fetchCart = async () => {
    try {
      const response = await apiClient.get('/crm-api/products/cart/');
      setCart(response.data);
    } catch (err) {
      console.error('Error fetching cart:', err);
    }
  };

  useEffect(() => {
    const ensureCsrf = async () => {
      try {
        console.log('[client-shop] Calling CSRF endpoint...');
        const response = await apiClient.get('/crm-api/products/csrf/');
        console.log('[client-shop] CSRF endpoint response:', response.data);
        const token = response.data.token;
        if (token) {
          setCsrfToken(token);
          console.log('[client-shop] CSRF token stored in state:', token.substring(0, 10) + '...');
        }
      } catch (e) {
        console.warn('[client-shop] Failed to prefetch CSRF token', e);
      }
    };

    ensureCsrf().finally(() => {
      fetchProducts();
      fetchCart();
    });
  }, []);

  // Add to cart
  const addToCart = async (productId: number, quantity: number = 1) => {
    setCartLoading(true);
    try {
      const config: any = {};
      if (csrfToken) {
        config.headers = { 'X-CSRFToken': csrfToken };
        console.log('[client-shop] Using CSRF token from state');
      }
      
      const response = await apiClient.post('/crm-api/products/cart/add/', {
        product_id: productId,
        quantity: quantity
      }, config);
      setCart(response.data.cart);
      setShowCart(true);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      alert(error.response?.data?.error || 'Failed to add item to cart');
    } finally {
      setCartLoading(false);
    }
  };

  // Update cart item quantity
  const updateCartItem = async (cartItemId: number, quantity: number) => {
    setCartLoading(true);
    try {
      const config: any = {};
      if (csrfToken) {
        config.headers = { 'X-CSRFToken': csrfToken };
      }
      
      const response = await apiClient.post('/crm-api/products/cart/update/', {
        cart_item_id: cartItemId,
        quantity: quantity
      }, config);
      setCart(response.data.cart);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      alert(error.response?.data?.error || 'Failed to update cart');
    } finally {
      setCartLoading(false);
    }
  };

  // Remove from cart
  const removeFromCart = async (cartItemId: number) => {
    setCartLoading(true);
    try {
      const config: any = {};
      if (csrfToken) {
        config.headers = { 'X-CSRFToken': csrfToken };
      }
      
      const response = await apiClient.post('/crm-api/products/cart/remove/', {
        cart_item_id: cartItemId
      }, config);
      setCart(response.data.cart);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      alert(error.response?.data?.error || 'Failed to remove item from cart');
    } finally {
      setCartLoading(false);
    }
  };

  // Clear cart
  const clearCart = async () => {
    if (!confirm('Are you sure you want to clear your cart?')) return;
    setCartLoading(true);
    try {
      const config: any = {};
      if (csrfToken) {
        config.headers = { 'X-CSRFToken': csrfToken };
      }
      
      const response = await apiClient.post('/crm-api/products/cart/clear/', {}, config);
      setCart(response.data.cart);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      alert(error.response?.data?.error || 'Failed to clear cart');
    } finally {
      setCartLoading(false);
    }
  };

  const categories: string[] = ['all', ...Array.from(new Set(products.map(p => p.category?.name).filter((name): name is string => Boolean(name))))];
  
  const filteredProducts = products.filter((p) => {
    // Filter by category
    if (selectedCategory !== 'all') {
      if (!p.category || p.category.name !== selectedCategory) {
        return false;
      }
    }
    // Filter by availability
    if (showAvailableOnly && p.stock_quantity === 0) {
      return false;
    }
    // Filter by search query (name or description)
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      return (
        p.name.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link href="/" className="flex items-center space-x-2 text-gray-700 hover:text-gray-900">
                <FiHome className="w-5 h-5" />
                <span className="font-medium">Home</span>
              </Link>
              <span className="text-gray-300">|</span>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Hanna Digital Shop
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowAssistant((v) => !v)}
                className="relative flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <FiZap className="w-5 h-5" />
                <span className="font-medium">AI Shopping Assistant</span>
              </button>
              <button
                onClick={() => setShowCart(!showCart)}
                className="relative flex items-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
              >
                <FiShoppingCart className="w-5 h-5" />
                <span className="font-medium">Cart</span>
                {cart && cart.total_items > 0 && (
                  <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                    {cart.total_items}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* AI Shopping Assistant */}
        {showAssistant && (
        <section className="mb-10 relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-600 to-white shadow-xl">
          <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(circle_at_20%_20%,#3b82f6,transparent_25%),radial-gradient(circle_at_80%_0%,#60a5fa,transparent_30%),radial-gradient(circle_at_50%_80%,#93c5fd,transparent_30%)]" aria-hidden="true"></div>
          <button
            aria-label="Close AI Assistant"
            onClick={() => setShowAssistant(false)}
            className="absolute top-4 right-4 z-10 inline-flex items-center justify-center rounded-full bg-white/80 text-gray-700 hover:bg-white shadow px-3 py-2"
          >
            <FiX className="w-5 h-5" />
          </button>
          <div ref={assistantRef} className="relative p-6 sm:p-8 grid gap-6 md:grid-cols-[1.1fr,1fr] items-center">
            <div className="space-y-4">
              <div className="inline-flex items-center px-3 py-1 rounded-full bg-blue-700/20 border border-blue-700/30 text-sm font-semibold text-blue-900">
                <FiZap className="mr-2" /> AI Shopping Assistant
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold leading-tight text-gray-900">Get tailored solar recommendations in minutes</h2>
              <p className="text-gray-700 max-w-xl">Use our AI assistant to size your system, compare bundles, and get cart-ready suggestions based on your exact appliances and budget.</p>
              <div className="flex flex-wrap gap-2">
                {assistantQuickPrompts.map((preset) => (
                  <button
                    key={preset.label}
                    onClick={() => launchAssistant(preset.prompt)}
                    className="px-4 py-2 rounded-full bg-blue-700/15 hover:bg-blue-700/25 border border-blue-700/30 text-sm font-semibold text-blue-900 backdrop-blur transition-colors"
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
              {!whatsappNumber && (
                <div className="inline-flex items-center gap-2 text-xs font-medium text-amber-800 bg-amber-100 border border-amber-300 rounded-full px-3 py-1">
                  <FiCopy className="w-4 h-4" /> Add NEXT_PUBLIC_WHATSAPP_NUMBER to enable direct WhatsApp launch; we will copy the message instead.
                </div>
              )}
            </div>

            <div className="bg-white text-gray-900 rounded-xl shadow-lg p-4 sm:p-5 border border-white/50">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-indigo-700"><FiMessageCircle /></span>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-gray-500">Prompt</p>
                    <p className="text-sm font-semibold text-gray-900">What do you need?</p>
                  </div>
                </div>
              </div>
              <div className="space-y-3">
                <textarea
                  value={assistantPrompt}
                  onChange={(e) => setAssistantPrompt(e.target.value)}
                  rows={4}
                  className="w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="Describe your appliances, hours of use, and budget..."
                />
                <div className="flex flex-col sm:flex-row gap-2">
                  <button
                    onClick={() => launchAssistant(assistantPrompt)}
                    className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition-colors"
                  >
                    <FiExternalLink className="w-4 h-4" /> Start in WhatsApp
                  </button>
                  <button
                    onClick={() => copyAssistantPrompt(assistantPrompt)}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-sm font-semibold text-gray-700 hover:bg-gray-50"
                  >
                    <FiCopy className="w-4 h-4" /> {assistantCopyStatus === 'copied' ? 'Copied' : 'Copy prompt'}
                  </button>
                </div>
                <p className="text-xs text-gray-500">We send this to the AI assistant. Mention appliances, runtime, and budget for the best recommendation.</p>
              </div>
            </div>
          </div>
        </section>
        )}

        {/* Search and Filter Controls */}
        <div className="mb-8 space-y-4">
          {/* Search Bar */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Search products by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Clear
              </button>
            )}
          </div>

          {/* Availability and Category Filters */}
          <div className="flex flex-col sm:flex-row gap-4">
            {/* Availability Toggle */}
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showAvailableOnly}
                onChange={(e) => setShowAvailableOnly(e.target.checked)}
                className="w-4 h-4 text-indigo-600 rounded"
              />
              <span className="text-sm font-medium text-gray-700">In Stock Only</span>
            </label>

            {/* Active Filter Indicators */}
            {(searchQuery || showAvailableOnly) && (
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">Filters active:</span>
                {searchQuery && (
                  <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-1 rounded-full">
                    Search: "{searchQuery}"
                  </span>
                )}
                {showAvailableOnly && (
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                    In Stock
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Category Filter */}
          <div className="pt-2">
            <p className="text-sm font-medium text-gray-700 mb-2">Filter by Category:</p>
            <div className="flex flex-wrap gap-2">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    selectedCategory === category
                      ? 'bg-indigo-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-200'
                  }`}
                >
                  {category === 'all' ? '✓ All Products' : category}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results Counter */}
        <div className="mb-6 flex items-center justify-between">
          <p className="text-sm text-gray-600">
            Showing <span className="font-semibold text-gray-900">{filteredProducts.length}</span> of{' '}
            <span className="font-semibold text-gray-900">{products.length}</span> products
          </p>
        </div>

        {/* Products Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading products...</p>
            </div>
          </div>
        ) : error ? (
          <div className="text-center py-20">
            <FiPackage className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-red-600 text-lg">{error}</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="text-center py-20">
            <FiPackage className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No products available</p>
          </div>
        ) : (
          <div>
            {/* Group products by category */}
            {(() => {
              const groupedByCategory = filteredProducts.reduce((acc: { [key: string]: Product[] }, product) => {
                const categoryName = product.category?.name || 'Uncategorized';
                if (!acc[categoryName]) {
                  acc[categoryName] = [];
                }
                acc[categoryName].push(product);
                return acc;
              }, {});
              
              return Object.entries(groupedByCategory).map(([categoryName, categoryProducts]) => (
                <div key={categoryName} className="mb-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6">{categoryName}</h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {categoryProducts.map((product) => (
                      <div
                        key={product.id}
                        className="bg-white rounded-xl shadow-md hover:shadow-xl transition-shadow duration-300 overflow-hidden"
                      >
                        <div className="h-48 bg-gradient-to-br from-indigo-100 to-purple-100 flex items-center justify-center overflow-hidden">
                          {product.images && product.images.length > 0 ? (
                            <img
                              src={product.images[0].image}
                              alt={product.images[0].alt_text || product.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <FiPackage className="w-16 h-16 text-indigo-400" />
                          )}
                        </div>
                        <div className="p-4">
                          <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{product.name}</h3>
                          {product.description && (
                            <p className="text-sm text-gray-600 mb-3 line-clamp-2">{product.description}</p>
                          )}
                          <div className="flex items-center justify-between mb-4">
                            <span className="text-2xl font-bold text-indigo-600">
                              {product.currency} {parseFloat(product.price).toFixed(2)}
                            </span>
                            {product.stock_quantity > 0 ? (
                              <span className="text-xs text-green-600 font-medium">In Stock</span>
                            ) : (
                              <span className="text-xs text-red-600 font-medium">Out of Stock</span>
                            )}
                          </div>
                          <button
                            onClick={() => addToCart(product.id)}
                            disabled={product.stock_quantity === 0 || cartLoading}
                            className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                          >
                            <FiShoppingCart className="w-4 h-4" />
                            <span>{product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ));
            })()}
          </div>
        )}
      </main>

      {/* Cart Sidebar */}
      {showCart && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => setShowCart(false)}></div>
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-xl">
            <div className="flex flex-col h-full">
              {/* Cart Header */}
              <div className="flex items-center justify-between p-6 border-b">
                <h2 className="text-2xl font-bold text-gray-900">Shopping Cart</h2>
                <button
                  onClick={() => setShowCart(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <FiX className="w-6 h-6" />
                </button>
              </div>

              {/* Cart Items */}
              <div className="flex-1 overflow-y-auto p-6">
                {!cart || cart.items.length === 0 ? (
                  <div className="text-center py-12">
                    <FiShoppingCart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600">Your cart is empty</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {cart.items.map((item) => (
                      <div key={item.id} className="flex items-start space-x-4 p-4 bg-gray-50 rounded-lg">
                        <div className="w-16 h-16 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FiPackage className="w-8 h-8 text-indigo-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-medium text-gray-900 mb-1">{item.product.name}</h3>
                          <p className="text-sm text-gray-600 mb-2">
                            {item.product.currency} {parseFloat(item.product.price).toFixed(2)} each
                          </p>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => updateCartItem(item.id, item.quantity - 1)}
                              disabled={cartLoading || item.quantity <= 1}
                              className="p-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50"
                            >
                              <FiMinus className="w-4 h-4" />
                            </button>
                            <span className="font-medium text-gray-900 w-8 text-center">{item.quantity}</span>
                            <button
                              onClick={() => updateCartItem(item.id, item.quantity + 1)}
                              disabled={cartLoading || item.quantity >= item.product.stock_quantity}
                              className="p-1 rounded bg-gray-200 hover:bg-gray-300 disabled:opacity-50"
                            >
                              <FiPlus className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => removeFromCart(item.id)}
                              disabled={cartLoading}
                              className="ml-auto p-1 text-red-600 hover:bg-red-50 rounded"
                            >
                              <FiTrash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-900">
                            {item.product.currency} {parseFloat(item.subtotal).toFixed(2)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Cart Footer */}
              {cart && cart.items.length > 0 && (
                <div className="border-t p-6 space-y-4">
                  <div className="flex items-center justify-between text-lg">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="text-2xl font-bold text-indigo-600">
                      USD {parseFloat(cart.total_price).toFixed(2)}
                    </span>
                  </div>
                  <button
                    disabled={cartLoading}
                    className="w-full px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold transition-colors disabled:bg-gray-400"
                  >
                    Proceed to Checkout
                  </button>
                  <button
                    onClick={clearCart}
                    disabled={cartLoading}
                    className="w-full px-6 py-2 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                  >
                    Clear Cart
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
