'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { FiShoppingCart, FiPlus, FiMinus, FiTrash2, FiPackage, FiHome, FiX } from 'react-icons/fi';
import axios from 'axios';
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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'https://backend.hanna.co.zw';

export default function PublicShopPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [cartLoading, setCartLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCart, setShowCart] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showAvailableOnly, setShowAvailableOnly] = useState<boolean>(false);
  
  // Checkout state
  const [checkoutStep, setCheckoutStep] = useState<number>(1); // 1: Cart, 2: Details, 3: Confirmation
  const [deliveryDetails, setDeliveryDetails] = useState({
    fullName: '',
    email: '',
    phone: '',
    address: '',
    city: '',
    notes: ''
  });

  // Fetch products
  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/crm-api/products/products/`, { withCredentials: true });
      // Normalize paginated response and filter active products
      const productsData = normalizePaginatedResponse<Product>(response.data);
      setProducts(productsData.filter((p: Product) => p.is_active));
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
      const response = await axios.get(`${API_BASE_URL}/crm-api/products/cart/`, { withCredentials: true });
      setCart(response.data);
    } catch (err) {
      console.error('Error fetching cart:', err);
    }
  };

  useEffect(() => {
    fetchProducts();
    fetchCart();
  }, []);

  // Add to cart
  const addToCart = async (productId: number, quantity: number = 1) => {
    setCartLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/crm-api/products/cart/add/`, {
        product_id: productId,
        quantity: quantity
      }, { withCredentials: true });
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
      const response = await axios.post(`${API_BASE_URL}/crm-api/products/cart/update/`, {
        cart_item_id: cartItemId,
        quantity: quantity
      }, { withCredentials: true });
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
      const response = await axios.post(`${API_BASE_URL}/crm-api/products/cart/remove/`, {
        cart_item_id: cartItemId
      }, { withCredentials: true });
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
      const response = await axios.post(`${API_BASE_URL}/crm-api/products/cart/clear/`);
      setCart(response.data.cart);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { error?: string } } };
      alert(error.response?.data?.error || 'Failed to clear cart');
    } finally {
      setCartLoading(false);
    }
  };

  // Handle delivery details input change
  const handleDeliveryChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setDeliveryDetails({
      ...deliveryDetails,
      [e.target.name]: e.target.value
    });
  };

  // Proceed to next checkout step
  const proceedToNextStep = () => {
    if (checkoutStep === 1) {
      setCheckoutStep(2);
    } else if (checkoutStep === 2) {
      // Validate delivery details
      if (!deliveryDetails.fullName || !deliveryDetails.email || !deliveryDetails.phone || !deliveryDetails.address) {
        alert('Please fill in all required fields');
        return;
      }
      setCheckoutStep(3);
    }
  };

  // Place order
  const placeOrder = async () => {
    setCartLoading(true);
    try {
      // Here you would call your order creation API
      alert('Order placed successfully! (Order creation API to be implemented)');
      setCheckoutStep(1);
      setShowCart(false);
      await clearCart();
    } catch (err) {
      alert('Failed to place order');
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
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredProducts.map((product) => (
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
                      <span className="text-xs text-green-600 font-medium">
                        {product.stock_quantity} in stock
                      </span>
                    ) : (
                      <span className="text-xs text-red-600 font-medium">Out of stock</span>
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
        )}
      </main>

      {/* Cart/Checkout Sidebar */}
      {showCart && (
        <div className="fixed inset-0 z-50 overflow-hidden">
          <div className="absolute inset-0 bg-black bg-opacity-50" onClick={() => { setShowCart(false); setCheckoutStep(1); }}></div>
          <div className="absolute right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-xl">
            <div className="flex flex-col h-full">
              {/* Header with Steps */}
              <div className="p-6 border-b">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {checkoutStep === 1 && 'Shopping Cart'}
                    {checkoutStep === 2 && 'Delivery Details'}
                    {checkoutStep === 3 && 'Order Confirmation'}
                  </h2>
                  <button
                    onClick={() => { setShowCart(false); setCheckoutStep(1); }}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <FiX className="w-6 h-6" />
                  </button>
                </div>
                
                {/* Step Indicators */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${checkoutStep >= 1 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                      1
                    </div>
                    <span className="ml-2 text-sm font-medium text-gray-700">Cart</span>
                  </div>
                  <div className={`flex-1 h-1 mx-2 ${checkoutStep >= 2 ? 'bg-indigo-600' : 'bg-gray-200'}`}></div>
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${checkoutStep >= 2 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                      2
                    </div>
                    <span className="ml-2 text-sm font-medium text-gray-700">Details</span>
                  </div>
                  <div className={`flex-1 h-1 mx-2 ${checkoutStep >= 3 ? 'bg-indigo-600' : 'bg-gray-200'}`}></div>
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${checkoutStep >= 3 ? 'bg-indigo-600 text-white' : 'bg-gray-200 text-gray-600'}`}>
                      3
                    </div>
                    <span className="ml-2 text-sm font-medium text-gray-700">Confirm</span>
                  </div>
                </div>
              </div>

              {/* Step Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {/* Step 1: Cart Items */}
                {checkoutStep === 1 && (
                  <>
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
                  </>
                )}

                {/* Step 2: Delivery Details */}
                {checkoutStep === 2 && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Full Name <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        name="fullName"
                        value={deliveryDetails.fullName}
                        onChange={handleDeliveryChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="John Doe"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Email <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="email"
                        name="email"
                        value={deliveryDetails.email}
                        onChange={handleDeliveryChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="john@example.com"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Phone Number <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="tel"
                        name="phone"
                        value={deliveryDetails.phone}
                        onChange={handleDeliveryChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="+1234567890"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Delivery Address <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        name="address"
                        value={deliveryDetails.address}
                        onChange={handleDeliveryChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="123 Main St, Apt 4B"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        City
                      </label>
                      <input
                        type="text"
                        name="city"
                        value={deliveryDetails.city}
                        onChange={handleDeliveryChange}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="New York"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Additional Notes
                      </label>
                      <textarea
                        name="notes"
                        value={deliveryDetails.notes}
                        onChange={handleDeliveryChange}
                        rows={3}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                        placeholder="Any special instructions..."
                      />
                    </div>
                  </div>
                )}

                {/* Step 3: Order Confirmation */}
                {checkoutStep === 3 && cart && (
                  <div className="space-y-6">
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <p className="text-green-800 font-medium">✓ Ready to place your order</p>
                    </div>
                    
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Delivery Information</h3>
                      <div className="bg-gray-50 rounded-lg p-4 space-y-2 text-sm">
                        <p><span className="font-medium">Name:</span> {deliveryDetails.fullName}</p>
                        <p><span className="font-medium">Email:</span> {deliveryDetails.email}</p>
                        <p><span className="font-medium">Phone:</span> {deliveryDetails.phone}</p>
                        <p><span className="font-medium">Address:</span> {deliveryDetails.address}</p>
                        {deliveryDetails.city && <p><span className="font-medium">City:</span> {deliveryDetails.city}</p>}
                        {deliveryDetails.notes && <p><span className="font-medium">Notes:</span> {deliveryDetails.notes}</p>}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold text-gray-900 mb-2">Order Summary</h3>
                      <div className="space-y-2">
                        {cart.items.map((item) => (
                          <div key={item.id} className="flex justify-between text-sm">
                            <span className="text-gray-700">{item.quantity}x {item.product.name}</span>
                            <span className="font-medium text-gray-900">
                              {item.product.currency} {parseFloat(item.subtotal).toFixed(2)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer Actions */}
              {cart && cart.items.length > 0 && (
                <div className="border-t p-6 space-y-4">
                  <div className="flex items-center justify-between text-lg">
                    <span className="font-medium text-gray-700">Total:</span>
                    <span className="text-2xl font-bold text-indigo-600">
                      USD {parseFloat(cart.total_price).toFixed(2)}
                    </span>
                  </div>
                  
                  <div className="flex gap-2">
                    {checkoutStep > 1 && (
                      <button
                        onClick={() => setCheckoutStep(checkoutStep - 1)}
                        disabled={cartLoading}
                        className="flex-1 px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-semibold transition-colors disabled:bg-gray-400"
                      >
                        Back
                      </button>
                    )}
                    
                    {checkoutStep < 3 && (
                      <button
                        onClick={proceedToNextStep}
                        disabled={cartLoading}
                        className="flex-1 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-semibold transition-colors disabled:bg-gray-400"
                      >
                        Continue
                      </button>
                    )}
                    
                    {checkoutStep === 3 && (
                      <button
                        onClick={placeOrder}
                        disabled={cartLoading}
                        className="flex-1 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold transition-colors disabled:bg-gray-400"
                      >
                        Place Order
                      </button>
                    )}
                  </div>

                  {checkoutStep === 1 && (
                    <button
                      onClick={clearCart}
                      disabled={cartLoading}
                      className="w-full px-6 py-2 text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      Clear Cart
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
