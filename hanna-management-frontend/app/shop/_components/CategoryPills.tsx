'use client';

interface CategoryPillsProps {
  categories: string[];
  selected: string;
  onSelect: (cat: string) => void;
  productCounts: Record<string, number>;
  showAvailableOnly: boolean;
  onAvailableToggle: (v: boolean) => void;
}

export default function CategoryPills({
  categories,
  selected,
  onSelect,
  productCounts,
  showAvailableOnly,
  onAvailableToggle,
}: CategoryPillsProps) {
  return (
    <div className="mb-6">
      <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => onSelect(cat)}
            className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full border font-semibold text-sm transition ${
              selected === cat
                ? 'bg-purple-600 text-white border-purple-600 shadow-sm'
                : 'bg-white text-purple-700 border-purple-200 hover:bg-purple-50'
            }`}
          >
            <span>{cat === 'all' ? 'All Products' : cat}</span>
            {productCounts[cat] !== undefined && (
              <span
                className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                  selected === cat ? 'bg-white/20 text-white' : 'bg-sky-100 text-sky-700'
                }`}
              >
                {productCounts[cat]}
              </span>
            )}
          </button>
        ))}

        {/* Divider */}
        <div className="flex-shrink-0 w-px h-6 bg-gray-200" />

        {/* In Stock toggle */}
        <button
          onClick={() => onAvailableToggle(!showAvailableOnly)}
          className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-full border font-semibold text-sm transition ${
            showAvailableOnly
              ? 'bg-green-600 text-white border-green-600'
              : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
          }`}
        >
          <span className="w-3 h-3 rounded-full border-2 flex-shrink-0" style={{
            background: showAvailableOnly ? 'white' : 'transparent',
            borderColor: showAvailableOnly ? 'white' : '#9ca3af',
          }} />
          In Stock Only
        </button>
      </div>
    </div>
  );
}
