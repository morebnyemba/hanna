import { FiSun, FiWifi, FiPackage, FiMonitor, FiHome, FiGrid, FiFeather, FiAward } from 'react-icons/fi';
import type { CategoryConfig } from '../_components/CategoryShopLayout';

const SHOP: { label: string; href: string } = { label: 'Shop', href: '/shop' };

export const SOLAR_CONFIG: CategoryConfig = {
  title: 'Solar Products',
  subtitle: 'Power your home and business',
  description: 'Solar panels, batteries, inverters and complete solar packages. Designed for Zimbabwe\'s climate.',
  searchTerms: ['solar', 'panel', 'battery', 'inverter', 'photovoltaic', 'pv', 'off-grid', 'hybrid'],
  theme: {
    gradient: 'from-orange-500 to-amber-400',
    badge: 'bg-orange-600',
    accent: 'text-orange-600',
    ring: 'border-orange-200 focus:ring-orange-400',
    light: 'bg-orange-50',
  },
  icon: <FiSun />,
  breadcrumb: [SHOP],
};

export const FURNITURE_CONFIG: CategoryConfig = {
  title: 'Furniture',
  subtitle: 'Premium pieces for every room',
  description: 'Custom-crafted furniture built to last — from fitted kitchens to luxury bedroom suites.',
  searchTerms: ['furniture', 'sofa', 'couch', 'table', 'chair', 'wardrobe', 'cabinet', 'shelf', 'bed', 'desk'],
  theme: {
    gradient: 'from-purple-700 to-violet-500',
    badge: 'bg-purple-700',
    accent: 'text-purple-700',
    ring: 'border-purple-200 focus:ring-purple-400',
    light: 'bg-purple-50',
  },
  icon: <FiPackage />,
  breadcrumb: [SHOP],
};

export const FURNITURE_FITTED_CONFIG: CategoryConfig = {
  title: 'Fitted Furniture',
  subtitle: 'Built-in solutions for every space',
  description: 'Custom fitted wardrobes, built-in cabinets and bespoke storage solutions measured precisely for your home.',
  searchTerms: ['fitted', 'built-in', 'wardrobe', 'closet', 'cabinet', 'storage', 'bespoke'],
  theme: {
    gradient: 'from-purple-700 to-violet-500',
    badge: 'bg-purple-700',
    accent: 'text-purple-700',
    ring: 'border-purple-200 focus:ring-purple-400',
    light: 'bg-purple-50',
  },
  icon: <FiGrid />,
  breadcrumb: [SHOP, { label: 'Furniture', href: '/shop/furniture' }],
};

export const FURNITURE_BEDROOM_CONFIG: CategoryConfig = {
  title: 'Bedroom Furniture',
  subtitle: 'Rest in style',
  description: 'Beds, dressers, bedside tables and complete bedroom suites. Crafted for comfort and style.',
  searchTerms: ['bedroom', 'bed', 'mattress', 'dresser', 'bedside', 'nightstand', 'headboard'],
  theme: {
    gradient: 'from-purple-600 to-pink-500',
    badge: 'bg-purple-600',
    accent: 'text-purple-600',
    ring: 'border-purple-200 focus:ring-purple-400',
    light: 'bg-purple-50',
  },
  icon: <FiHome />,
  breadcrumb: [SHOP, { label: 'Furniture', href: '/shop/furniture' }],
};

export const FURNITURE_KITCHEN_CONFIG: CategoryConfig = {
  title: 'Kitchen Furniture',
  subtitle: 'The heart of your home',
  description: 'Kitchen cabinets, countertops, islands and fitted kitchens. Functional designs that last a lifetime.',
  searchTerms: ['kitchen', 'cabinet', 'countertop', 'island', 'pantry', 'cupboard'],
  theme: {
    gradient: 'from-amber-600 to-orange-400',
    badge: 'bg-amber-600',
    accent: 'text-amber-700',
    ring: 'border-amber-200 focus:ring-amber-400',
    light: 'bg-amber-50',
  },
  icon: <FiGrid />,
  breadcrumb: [SHOP, { label: 'Furniture', href: '/shop/furniture' }],
};

export const FURNITURE_LUXURY_CONFIG: CategoryConfig = {
  title: 'Luxury Furniture',
  subtitle: 'Premium craftsmanship, exceptional design',
  description: 'Our finest handcrafted pieces — premium materials, bespoke finishes and timeless design for discerning tastes.',
  searchTerms: ['luxury', 'premium', 'executive', 'designer', 'bespoke', 'handcrafted', 'leather'],
  theme: {
    gradient: 'from-slate-800 to-purple-900',
    badge: 'bg-slate-700',
    accent: 'text-slate-700',
    ring: 'border-slate-200 focus:ring-slate-400',
    light: 'bg-slate-50',
  },
  icon: <FiAward />,
  breadcrumb: [SHOP, { label: 'Furniture', href: '/shop/furniture' }],
};

export const STARLINK_CONFIG: CategoryConfig = {
  title: 'Starlink',
  subtitle: 'High-speed satellite internet',
  description: 'Starlink kits, accessories and installation services. Reliable internet wherever you are in Zimbabwe.',
  searchTerms: ['starlink', 'satellite', 'internet', 'wifi', 'router', 'dish', 'broadband'],
  theme: {
    gradient: 'from-sky-600 to-blue-500',
    badge: 'bg-sky-600',
    accent: 'text-sky-600',
    ring: 'border-sky-200 focus:ring-sky-400',
    light: 'bg-sky-50',
  },
  icon: <FiWifi />,
  breadcrumb: [SHOP],
};

export const TECH_CONFIG: CategoryConfig = {
  title: 'Tech & Electronics',
  subtitle: 'The latest in technology',
  description: 'Electronics, smart home devices, accessories and the latest gadgets — curated for Zimbabwe.',
  searchTerms: ['tech', 'electronics', 'gadget', 'smart', 'device', 'computer', 'phone', 'laptop', 'accessory'],
  theme: {
    gradient: 'from-green-600 to-teal-500',
    badge: 'bg-green-600',
    accent: 'text-green-700',
    ring: 'border-green-200 focus:ring-green-400',
    light: 'bg-green-50',
  },
  icon: <FiMonitor />,
  breadcrumb: [SHOP],
};
