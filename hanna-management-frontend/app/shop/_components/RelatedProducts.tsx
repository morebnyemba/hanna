'use client';

import { FiPackage, FiShoppingCart } from 'react-icons/fi';
import type { Product } from './ProductCard';

interface RelatedProductsProps {
  currentProduct: Product;
  allProducts: Product[];
  onSelect: (product: Product) => void;
  onAddToCart: (id: number) => void;
}

export default function RelatedProducts({ currentProduct, allProducts, onSelect, onAddToCart }: RelatedProductsProps) {
  const related = allProducts
    .filter((p) =>
      p.id !== currentProduct.id &&
      p.is_active &&
      (
        (currentProduct.category && p.category?.id === currentProduct.category.id) ||
        p.product_type === currentProduct.product_type
      )
    )
    .slice(0, 4);

  if (related.length === 0) return null;

  return (
    <div className="mt-6 pt-5 border-t border-purple-100">
      <h3 className="text-sm font-extrabold text-sky-900 uppercase tracking-wider mb-3">You May Also Like</h3>
      <div className="grid grid-cols-2 gap-3">
        {related.map((product) => {
          const price = parseFloat(product.price);
          return (
            <button
              key={product.id}
              onClick={() => onSelect(product)}
              className="text-left bg-gray-50 hover:bg-sky-50 rounded-xl p-3 border border-gray-100 hover:border-sky-200 transition-all group"
            >
              <div className="h-20 bg-white rounded-lg flex items-center justify-center overflow-hidden mb-2 border border-gray-100">
                {product.images && product.images.length > 0 ? (
                  <img src={product.images[0].image} alt={product.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform" loading="lazy" />
                ) : (
                  <FiPackage className="w-6 h-6 text-sky-300" />
                )}
              </div>
              <p className="text-xs font-bold text-sky-900 line-clamp-2 leading-snug mb-1">{product.name}</p>
              <div className="flex items-center justify-between">
                <p className="text-sm font-extrabold text-orange-500">{product.currency} {isNaN(price) ? '—' : price.toFixed(2)}</p>
                <button
                  onClick={(e) => { e.stopPropagation(); onAddToCart(product.id); }}
                  disabled={product.stock_quantity === 0}
                  className="w-6 h-6 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-200 text-white rounded-full flex items-center justify-center transition flex-shrink-0"
                >
                  <FiShoppingCart className="w-3 h-3" />
                </button>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
