'use client';

import { FiPackage } from 'react-icons/fi';
import ProductCard, { type Product } from './ProductCard';

interface ProductGridProps {
  products: Product[];
  loading: boolean;
  error: string | null;
  selectedCategory: string;
  onAddToCart: (id: number) => void;
  onQuickView: (product: Product) => void;
  cartLoading: boolean;
}

export default function ProductGrid({
  products,
  loading,
  error,
  selectedCategory,
  onAddToCart,
  onQuickView,
  cartLoading,
}: ProductGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="bg-white rounded-2xl border border-purple-100 overflow-hidden animate-pulse">
            <div className="h-44 bg-purple-50" />
            <div className="p-4 space-y-3">
              <div className="h-3 bg-purple-100 rounded w-2/3" />
              <div className="h-4 bg-purple-100 rounded" />
              <div className="h-3 bg-purple-50 rounded w-3/4" />
              <div className="h-8 bg-orange-100 rounded-xl mt-4" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mb-4">
          <FiPackage className="w-8 h-8 text-red-400" />
        </div>
        <p className="text-red-600 font-semibold text-lg mb-1">Could not load products</p>
        <p className="text-gray-500 text-sm">{error}</p>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-16 h-16 rounded-full bg-purple-50 flex items-center justify-center mb-4">
          <FiPackage className="w-8 h-8 text-purple-300" />
        </div>
        <p className="text-gray-700 font-semibold text-lg mb-1">No products found</p>
        <p className="text-gray-400 text-sm">Try adjusting your filters or search query.</p>
      </div>
    );
  }

  // Group by category when showing all, flat grid when filtered
  if (selectedCategory === 'all') {
    const grouped = products.reduce<Record<string, Product[]>>((acc, p) => {
      const cat = p.category?.name || 'Other';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(p);
      return acc;
    }, {});

    return (
      <div className="space-y-10">
        {Object.entries(grouped).map(([cat, items]) => (
          <div key={cat}>
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-xl font-extrabold text-purple-900">{cat}</h2>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-600">{items.length}</span>
              <div className="flex-1 h-px bg-purple-100" />
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {items.map((p) => (
                <ProductCard key={p.id} product={p} onAddToCart={onAddToCart} onQuickView={onQuickView} cartLoading={cartLoading} />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm font-semibold text-gray-600">{products.length} result{products.length !== 1 ? 's' : ''}</span>
        {selectedCategory !== 'all' && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-semibold">{selectedCategory}</span>
        )}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
        {products.map((p) => (
          <ProductCard key={p.id} product={p} onAddToCart={onAddToCart} onQuickView={onQuickView} cartLoading={cartLoading} />
        ))}
      </div>
    </div>
  );
}
