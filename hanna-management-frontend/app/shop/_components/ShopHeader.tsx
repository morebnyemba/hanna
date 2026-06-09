'use client';

import Link from 'next/link';
import { FiShoppingCart, FiZap, FiMenu, FiSearch, FiX } from 'react-icons/fi';

interface ShopHeaderProps {
  cartItemCount: number;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onCartOpen: () => void;
  onAssistantToggle: () => void;
  showMobileMenu: boolean;
  onMobileMenuToggle: () => void;
  showAssistant: boolean;
}

export default function ShopHeader({
  cartItemCount,
  searchQuery,
  onSearchChange,
  onCartOpen,
  onAssistantToggle,
  showMobileMenu,
  onMobileMenuToggle,
  showAssistant,
}: ShopHeaderProps) {
  return (
    <header className="bg-white border-b border-purple-100 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main nav row */}
        <div className="flex items-center justify-between h-16 gap-4">
          {/* Logo */}
          <Link href="/shop" className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center shadow">
              <span className="text-white font-bold text-sm">H</span>
            </div>
            <span className="hidden sm:block font-bold text-purple-800 text-lg tracking-tight">Hanna</span>
          </Link>

          {/* Search — desktop */}
          <div className="hidden md:flex flex-1 max-w-xl relative">
            <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-sky-400 w-4 h-4 pointer-events-none" />
            <input
              type="text"
              placeholder="Search solar, furniture, Starlink…"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-9 pr-10 py-2 rounded-xl border border-sky-200 bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:bg-white text-sm text-gray-800 placeholder-sky-300 transition"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <FiX className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* AI Assistant — desktop */}
            <button
              onClick={onAssistantToggle}
              className={`hidden md:flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm transition ${
                showAssistant
                  ? 'bg-sky-600 text-white'
                  : 'bg-sky-50 text-sky-600 border border-sky-200 hover:bg-sky-100'
              }`}
            >
              <FiZap className="w-4 h-4" />
              <span>AI Assistant</span>
            </button>

            {/* Cart */}
            <button
              onClick={onCartOpen}
              className="relative flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl font-semibold text-sm transition shadow-sm"
            >
              <FiShoppingCart className="w-4 h-4" />
              <span className="hidden sm:inline">Cart</span>
              {cartItemCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                  {cartItemCount > 9 ? '9+' : cartItemCount}
                </span>
              )}
            </button>

            {/* Mobile menu button */}
            <button
              onClick={onMobileMenuToggle}
              className="md:hidden p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 transition"
              aria-label="Menu"
            >
              {showMobileMenu ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Search — mobile */}
        <div className="md:hidden pb-3 relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-sky-400 w-4 h-4 pointer-events-none" />
          <input
            type="text"
            placeholder="Search products…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-9 py-2 rounded-xl border border-sky-200 bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:bg-white text-sm text-gray-800 placeholder-sky-300"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400"
            >
              <FiX className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Mobile dropdown */}
        {showMobileMenu && (
          <div className="md:hidden pb-3 border-t border-purple-50 pt-3">
            <button
              onClick={() => { onAssistantToggle(); onMobileMenuToggle(); }}
              className="w-full flex items-center gap-2 px-4 py-3 bg-sky-50 text-sky-700 border border-sky-200 rounded-xl font-semibold text-sm hover:bg-sky-100 transition"
            >
              <FiZap className="w-4 h-4" />
              AI Shopping Assistant
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
