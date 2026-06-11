'use client';

import { FiPackage, FiTool, FiCpu, FiGrid, FiLayers, FiTag } from 'react-icons/fi';

// All product_type choices from the Django model — always shown even if count is 0
export const PRODUCT_TYPES = [
  { value: 'all',      label: 'All Types',  icon: <FiGrid className="w-3.5 h-3.5" /> },
  { value: 'hardware', label: 'Hardware',   icon: <FiPackage className="w-3.5 h-3.5" /> },
  { value: 'service',  label: 'Services',   icon: <FiTool className="w-3.5 h-3.5" /> },
  { value: 'software', label: 'Software',   icon: <FiCpu className="w-3.5 h-3.5" /> },
  { value: 'module',   label: 'Modules',    icon: <FiLayers className="w-3.5 h-3.5" /> },
] as const;

export type ProductTypeFilter = typeof PRODUCT_TYPES[number]['value'];

interface CategoryPillsProps {
  selected: ProductTypeFilter;
  onSelect: (type: ProductTypeFilter) => void;
  typeCounts: Record<string, number>;
  showAvailableOnly: boolean;
  onAvailableToggle: (v: boolean) => void;
  // Category filter
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
  return (
    <div className="mb-6 space-y-3">
      {/* Row 1: Type filter */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
        <span className="flex-shrink-0 text-xs font-bold text-gray-400 uppercase tracking-wider mr-1">Type</span>
        {PRODUCT_TYPES.map(({ value, label, icon }) => {
          const count = value === 'all'
            ? Object.values(typeCounts).reduce((a, b) => a + b, 0)
            : (typeCounts[value] ?? 0);
          const active = selected === value;
          return (
            <button
              key={value}
              onClick={() => onSelect(value)}
              className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border font-semibold text-sm transition-all ${
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

        <div className="flex-shrink-0 w-px h-6 bg-gray-200 mx-1" />

        <button
          onClick={() => onAvailableToggle(!showAvailableOnly)}
          className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border font-semibold text-sm transition-all ${
            showAvailableOnly
              ? 'bg-green-600 text-white border-green-600'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          <span className={`w-2.5 h-2.5 rounded-full border-2 flex-shrink-0 ${
            showAvailableOnly ? 'bg-white border-white' : 'bg-transparent border-gray-400'
          }`} />
          In Stock Only
        </button>
      </div>

      {/* Row 2: Category filter (dynamic) */}
      {categories.length > 0 && (
        <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-hide">
          <span className="flex-shrink-0 text-xs font-bold text-gray-400 uppercase tracking-wider mr-1">Category</span>
          <button
            onClick={() => onCategorySelect('all')}
            className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border font-semibold text-sm transition-all ${
              selectedCategory === 'all'
                ? 'bg-purple-600 text-white border-purple-600 shadow-sm'
                : 'bg-white text-purple-700 border-purple-200 hover:bg-purple-50 hover:border-purple-400'
            }`}
          >
            <FiGrid className="w-3.5 h-3.5" />
            <span>All</span>
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
              selectedCategory === 'all' ? 'bg-white/20 text-white' : 'bg-purple-100 text-purple-700'
            }`}>{Object.values(categoryCounts).reduce((a, b) => a + b, 0)}</span>
          </button>
          {categories.map((cat) => {
            const active = selectedCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => onCategorySelect(cat)}
                className={`flex-shrink-0 flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border font-semibold text-sm transition-all ${
                  active
                    ? 'bg-purple-600 text-white border-purple-600 shadow-sm'
                    : 'bg-white text-purple-700 border-purple-200 hover:bg-purple-50 hover:border-purple-400'
                }`}
              >
                <FiTag className="w-3.5 h-3.5" />
                <span>{cat}</span>
                <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                  active ? 'bg-white/20 text-white' : 'bg-purple-100 text-purple-700'
                }`}>{categoryCounts[cat] ?? 0}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
