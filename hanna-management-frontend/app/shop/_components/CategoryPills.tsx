'use client';

import { FiPackage, FiTool, FiCpu, FiGrid, FiLayers, FiSun, FiWifi, FiHome, FiMonitor, FiTag } from 'react-icons/fi';

export const PRODUCT_TYPES = [
  { value: 'all',      label: 'All',       icon: <FiGrid className="w-3.5 h-3.5" /> },
  { value: 'hardware', label: 'Hardware',  icon: <FiPackage className="w-3.5 h-3.5" /> },
  { value: 'service',  label: 'Services',  icon: <FiTool className="w-3.5 h-3.5" /> },
  { value: 'software', label: 'Software',  icon: <FiCpu className="w-3.5 h-3.5" /> },
  { value: 'module',   label: 'Modules',   icon: <FiLayers className="w-3.5 h-3.5" /> },
] as const;

export type ProductTypeFilter = typeof PRODUCT_TYPES[number]['value'];

function categoryIcon(name: string) {
  const n = name.toLowerCase();
  if (n.includes('solar') || n.includes('panel') || n.includes('battery')) return <FiSun className="w-3.5 h-3.5" />;
  if (n.includes('starlink') || n.includes('wifi') || n.includes('internet')) return <FiWifi className="w-3.5 h-3.5" />;
  if (n.includes('furniture') || n.includes('bedroom') || n.includes('kitchen') || n.includes('fitted') || n.includes('luxury')) return <FiHome className="w-3.5 h-3.5" />;
  if (n.includes('tech') || n.includes('computer') || n.includes('laptop')) return <FiMonitor className="w-3.5 h-3.5" />;
  return <FiTag className="w-3.5 h-3.5" />;
}

interface CategoryPillsProps {
  selected: ProductTypeFilter;
  onSelect: (type: ProductTypeFilter) => void;
  typeCounts: Record<string, number>;
  showAvailableOnly: boolean;
  onAvailableToggle: (v: boolean) => void;
  categories: string[];
  selectedCategory: string;
  onCategorySelect: (cat: string) => void;
  categoryCounts: Record<string, number>;
}

export default function CategoryPills({
  selected,
  onSelect,
  typeCounts,
  showAvailableOnly,
  onAvailableToggle,
  categories,
  selectedCategory,
  onCategorySelect,
  categoryCounts,
}: CategoryPillsProps) {
  const anyTypeActive = selected !== 'all';
  const anyCatActive = selectedCategory !== 'all';

  return (
    <div className="mb-6">
      <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-hide">

        {/* ── ALL ─────────────────────────────────────────── */}
        <button
          onClick={() => { onSelect('all'); onCategorySelect('all'); }}
          className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full border font-semibold text-sm transition-all ${
            !anyTypeActive && !anyCatActive
              ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
              : 'bg-white text-sky-700 border-sky-200 hover:bg-sky-50 hover:border-sky-400'
          }`}
        >
          <FiGrid className="w-3.5 h-3.5" />
          <span>All Products</span>
          <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
            !anyTypeActive && !anyCatActive ? 'bg-white/20 text-white' : 'bg-sky-100 text-sky-700'
          }`}>
            {Object.values(typeCounts).reduce((a, b) => a + b, 0)}
          </span>
        </button>

        {/* ── TYPE divider ─────────────────────────────────── */}
        <span className="flex-shrink-0 text-[10px] font-bold text-gray-300 uppercase tracking-widest px-1">Type</span>

        {PRODUCT_TYPES.filter(t => t.value !== 'all').map(({ value, label, icon }) => {
          const count = typeCounts[value] ?? 0;
          const active = selected === value;
          return (
            <button
              key={value}
              onClick={() => { onSelect(value); onCategorySelect('all'); }}
              className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-full border font-semibold text-sm transition-all ${
                active
                  ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                  : 'bg-white text-sky-700 border-sky-200 hover:bg-sky-50 hover:border-sky-400'
              }`}
            >
              {icon}
              <span>{label}</span>
              <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                active ? 'bg-white/20 text-white' : 'bg-sky-100 text-sky-700'
              }`}>{count}</span>
            </button>
          );
        })}

        {/* ── CATEGORY divider ─────────────────────────────── */}
        {categories.length > 0 && (
          <>
            <span className="flex-shrink-0 text-[10px] font-bold text-gray-300 uppercase tracking-widest px-1">Category</span>
            {categories.map((cat) => {
              const active = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  onClick={() => { onCategorySelect(cat); onSelect('all'); }}
                  className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-full border font-semibold text-sm transition-all ${
                    active
                      ? 'bg-orange-500 text-white border-orange-500 shadow-sm'
                      : 'bg-white text-orange-600 border-orange-200 hover:bg-orange-50 hover:border-orange-400'
                  }`}
                >
                  {categoryIcon(cat)}
                  <span>{cat}</span>
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                    active ? 'bg-white/20 text-white' : 'bg-orange-100 text-orange-600'
                  }`}>{categoryCounts[cat] ?? 0}</span>
                </button>
              );
            })}
          </>
        )}

        {/* ── IN STOCK divider ─────────────────────────────── */}
        <div className="flex-shrink-0 w-px h-6 bg-gray-200 mx-1" />
        <button
          onClick={() => onAvailableToggle(!showAvailableOnly)}
          className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-2 rounded-full border font-semibold text-sm transition-all ${
            showAvailableOnly
              ? 'bg-green-600 text-white border-green-600'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          <span className={`w-2.5 h-2.5 rounded-full border-2 flex-shrink-0 ${
            showAvailableOnly ? 'bg-white border-white' : 'bg-transparent border-gray-400'
          }`} />
          In Stock
        </button>

      </div>
    </div>
  );
}
