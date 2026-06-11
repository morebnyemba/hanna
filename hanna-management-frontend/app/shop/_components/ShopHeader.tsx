'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  FiShoppingCart, FiZap, FiMenu, FiSearch, FiX,
  FiSun, FiWifi, FiPackage, FiMonitor, FiChevronDown,
} from 'react-icons/fi';

interface NavFilter {
  search: string;
  category?: string;
}

interface ShopHeaderProps {
  cartItemCount: number;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onCartOpen: () => void;
  onAssistantToggle: () => void;
  showMobileMenu: boolean;
  onMobileMenuToggle: () => void;
  showAssistant: boolean;
  onNavFilter: (f: NavFilter) => void;
}

// ─── Nav config ───────────────────────────────────────────────────────────────

const NAV_ITEMS = [
  {
    label: 'Solar Products',
    icon: <FiSun className="w-4 h-4" />,
    href: '/shop/solar',
    filter: { search: 'solar' },
    color: 'text-orange-600',
    children: [
      { label: 'Solar Panels', href: '/shop/solar', filter: { search: 'solar panel' } },
      { label: 'Solar Batteries', href: '/shop/solar', filter: { search: 'solar battery' } },
      { label: 'Inverters', href: '/shop/solar', filter: { search: 'inverter' } },
      { label: 'Solar Packages', href: '/shop/solar', filter: { search: 'solar package' } },
    ],
  },
  {
    label: 'Furniture',
    icon: <FiPackage className="w-4 h-4" />,
    href: '/shop/furniture',
    filter: { search: 'furniture' },
    color: 'text-purple-600',
    children: [
      { label: 'All Furniture', href: '/shop/furniture', filter: { search: 'furniture' } },
      { label: 'Fitted Furniture', href: '/shop/furniture/fitted', filter: { search: 'fitted' } },
      { label: 'Bedroom', href: '/shop/furniture/bedroom', filter: { search: 'bedroom' } },
      { label: 'Kitchen', href: '/shop/furniture/kitchen', filter: { search: 'kitchen' } },
      { label: 'Luxury', href: '/shop/furniture/luxury', filter: { search: 'luxury' } },
    ],
  },
  {
    label: 'Starlink',
    icon: <FiWifi className="w-4 h-4" />,
    href: '/shop/starlink',
    filter: { search: 'starlink' },
    color: 'text-sky-600',
    children: [
      { label: 'Starlink Kits', href: '/shop/starlink', filter: { search: 'starlink kit' } },
      { label: 'Accessories', href: '/shop/starlink', filter: { search: 'starlink accessory' } },
      { label: 'Installation', href: '/shop/starlink', filter: { search: 'starlink install' } },
    ],
  },
  {
    label: 'Tech',
    icon: <FiMonitor className="w-4 h-4" />,
    href: '/shop/tech',
    filter: { search: 'tech' },
    color: 'text-green-600',
    children: [
      { label: 'Electronics', href: '/shop/tech', filter: { search: 'electronics' } },
      { label: 'Accessories', href: '/shop/tech', filter: { search: 'accessories' } },
      { label: 'Smart Home', href: '/shop/tech', filter: { search: 'smart' } },
    ],
  },
] as const;

// ─── Dropdown component ────────────────────────────────────────────────────────

function NavDropdown({
  item,
  onNavFilter,
}: {
  item: typeof NAV_ITEMS[number];
  onNavFilter: (f: NavFilter) => void;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleTopClick = () => {
    onNavFilter(item.filter as NavFilter);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={handleTopClick}
        onMouseEnter={() => setOpen(true)}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-xl font-semibold text-sm transition-all ${
          open ? 'bg-purple-50 text-purple-700' : `hover:bg-gray-50 ${item.color}`
        }`}
      >
        {item.icon}
        {item.label}
        <FiChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div
          className="absolute top-full left-0 mt-1 w-52 bg-white rounded-2xl shadow-xl border border-purple-100 py-2 z-50"
          onMouseLeave={() => setOpen(false)}
        >
          <button
            onClick={handleTopClick}
            className="w-full flex items-center gap-2 px-4 py-2.5 text-sm font-bold text-purple-800 hover:bg-purple-50 transition text-left"
          >
            {item.icon}
            All {item.label}
          </button>

          <div className="mx-3 border-t border-gray-100 my-1" />

          {item.children.map((child) => (
            <button
              key={child.label}
              onClick={() => { onNavFilter(child.filter as NavFilter); setOpen(false); }}
              className="w-full flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-purple-50 hover:text-purple-700 transition text-left"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-purple-300 mr-2 flex-shrink-0" />
              {child.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main header ──────────────────────────────────────────────────────────────

export default function ShopHeader({
  cartItemCount,
  searchQuery,
  onSearchChange,
  onCartOpen,
  onAssistantToggle,
  showMobileMenu,
  onMobileMenuToggle,
  showAssistant,
  onNavFilter,
}: ShopHeaderProps) {
  const [mobileExpandedItem, setMobileExpandedItem] = useState<string | null>(null);

  return (
    <header className="bg-white border-b border-purple-100 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* ── Top row: logo + search + actions ── */}
        <div className="flex items-center justify-between h-14 gap-3">
          {/* Logo */}
          <Link href="/shop" className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-600 to-purple-800 flex items-center justify-center shadow">
              <span className="text-white font-bold text-sm">H</span>
            </div>
            <span className="hidden sm:block font-extrabold text-purple-800 text-lg tracking-tight">Hanna</span>
          </Link>

          {/* Search — desktop */}
          <div className="hidden md:flex flex-1 max-w-lg relative">
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
            <button
              onClick={onAssistantToggle}
              className={`hidden md:flex items-center gap-1.5 px-3 py-2 rounded-xl font-semibold text-sm transition ${
                showAssistant
                  ? 'bg-sky-600 text-white'
                  : 'bg-sky-50 text-sky-600 border border-sky-200 hover:bg-sky-100'
              }`}
            >
              <FiZap className="w-4 h-4" />
              AI
            </button>

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

            <button
              onClick={onMobileMenuToggle}
              className="md:hidden p-2 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-600 transition"
              aria-label="Menu"
            >
              {showMobileMenu ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* ── Nav row (desktop) ── */}
        <div className="hidden md:flex items-center gap-1 pb-2 border-t border-purple-50 pt-2">
          {NAV_ITEMS.map((item) => (
            <NavDropdown key={item.label} item={item} onNavFilter={onNavFilter} />
          ))}
          <div className="ml-auto flex items-center gap-2 text-xs text-gray-400">
            <span className="hidden lg:block">🇿🇼 Delivering Nationwide</span>
            <Link href="/portals" className="text-purple-500 hover:text-purple-700 font-semibold hover:underline">
              Business Portals →
            </Link>
          </div>
        </div>

        {/* ── Search row (mobile) ── */}
        <div className="md:hidden pb-2 relative">
          <FiSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-sky-400 w-4 h-4 pointer-events-none" />
          <input
            type="text"
            placeholder="Search products…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-9 pr-9 py-2 rounded-xl border border-sky-200 bg-sky-50 focus:outline-none focus:ring-2 focus:ring-sky-400 focus:bg-white text-sm text-gray-800 placeholder-sky-300"
          />
          {searchQuery && (
            <button onClick={() => onSearchChange('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">
              <FiX className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* ── Mobile menu ── */}
        {showMobileMenu && (
          <div className="md:hidden border-t border-purple-50 pt-3 pb-4 space-y-1">
            {/* AI assistant */}
            <button
              onClick={() => { onAssistantToggle(); onMobileMenuToggle(); }}
              className="w-full flex items-center gap-2 px-4 py-3 bg-sky-50 text-sky-700 border border-sky-200 rounded-xl font-semibold text-sm hover:bg-sky-100 transition"
            >
              <FiZap className="w-4 h-4" />
              AI Shopping Assistant
            </button>

            {/* Nav items */}
            {NAV_ITEMS.map((item) => (
              <div key={item.label}>
                <button
                  onClick={() => setMobileExpandedItem(mobileExpandedItem === item.label ? null : item.label)}
                  className={`w-full flex items-center justify-between px-4 py-3 rounded-xl text-sm font-semibold transition ${
                    mobileExpandedItem === item.label ? 'bg-purple-50 text-purple-700' : 'hover:bg-gray-50 text-gray-700'
                  }`}
                >
                  <span className="flex items-center gap-2">{item.icon}{item.label}</span>
                  <FiChevronDown className={`w-4 h-4 transition-transform ${mobileExpandedItem === item.label ? 'rotate-180' : ''}`} />
                </button>

                {mobileExpandedItem === item.label && (
                  <div className="ml-4 mt-1 space-y-0.5 border-l-2 border-purple-100 pl-3">
                    {item.children.map((child) => (
                      <button
                        key={child.label}
                        onClick={() => { onNavFilter(child.filter as NavFilter); onMobileMenuToggle(); setMobileExpandedItem(null); }}
                        className="w-full text-left block px-3 py-2 text-sm text-gray-600 hover:text-purple-700 hover:bg-purple-50 rounded-lg transition"
                      >
                        {child.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}

            <Link href="/portals" className="block px-4 py-3 text-sm text-purple-600 font-semibold hover:bg-purple-50 rounded-xl transition">
              Business Portals →
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}
