'use client';

import { FiPackage } from 'react-icons/fi';
import type { Product } from './ProductCard';

interface RecentlyViewedProps {
  products: Product[];
  onSelect: (product: Product) => void;
}

export default function RecentlyViewed({ products, onSelect }: RecentlyViewedProps) {
  if (products.length === 0) return null;

  return (
    <section className="mt-12 mb-6">
      <h2 className="text-lg font-extrabold text-sky-900 mb-4">Recently Viewed</h2>
      <div className="flex gap-4 overflow-x-auto pb-3 scrollbar-hide">
        {products.map((product) => {
          const price = parseFloat(product.price);
          return (
            <button
              key={product.id}
              onClick={() => onSelect(product)}
              className="flex-shrink-0 w-44 bg-white rounded-2xl border border-sky-100 shadow-sm hover:shadow-md hover:border-sky-300 transition-all overflow-hidden text-left group"
            >
              <div className="h-28 bg-gradient-to-br from-sky-50 to-purple-50 flex items-center justify-center overflow-hidden">
                {product.images && product.images.length > 0 ? (
                  <img
                    src={product.images[0].image}
                    alt={product.name}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    loading="lazy"
                  />
                ) : (
                  <FiPackage className="w-8 h-8 text-sky-300" />
                )}
              </div>
              <div className="p-3">
                <p className="text-xs font-bold text-sky-900 line-clamp-2 leading-snug mb-1">{product.name}</p>
                <p className="text-sm font-extrabold text-orange-500">
                  {product.currency} {isNaN(price) ? '—' : price.toFixed(2)}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
