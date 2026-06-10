'use client';

import { FiShoppingCart, FiPackage, FiEye, FiSun, FiWifi } from 'react-icons/fi';

export interface Product {
  id: number;
  name: string;
  description: string;
  short_description?: string;
  price: string;
  currency: string;
  is_active: boolean;
  stock_quantity: number;
  product_type: string;
  featured?: boolean;
  brand?: string;
  sku?: string;
  category: { id: number; name: string } | null;
  images?: Array<{ id: number; image: string; alt_text?: string }>;
}

interface ProductCardProps {
  product: Product;
  onAddToCart: (id: number) => void;
  onQuickView: (product: Product) => void;
  cartLoading: boolean;
}

function CategoryIcon({ category }: { category: string | null }) {
  const name = (category || '').toLowerCase();
  if (name.includes('solar') || name.includes('panel') || name.includes('battery'))
    return <FiSun className="w-10 h-10 text-orange-300" />;
  if (name.includes('starlink') || name.includes('wifi') || name.includes('internet'))
    return <FiWifi className="w-10 h-10 text-sky-300" />;
  return <FiPackage className="w-10 h-10 text-purple-300" />;
}

function StockBadge({ qty }: { qty: number }) {
  if (qty === 0)
    return <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-600">Out of Stock</span>;
  if (qty <= 5)
    return <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-orange-100 text-orange-600">Low Stock</span>;
  return <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-green-100 text-green-700">In Stock</span>;
}

export default function ProductCard({ product, onAddToCart, onQuickView, cartLoading }: ProductCardProps) {
  const preview = product.short_description || product.description || '';
  const price = parseFloat(product.price);

  return (
    <div
      className="shop-fade-up group bg-white rounded-2xl border border-purple-100 shadow-sm hover:shadow-lg hover:border-purple-300 transition-all duration-300 overflow-hidden flex flex-col cursor-pointer"
      onClick={() => onQuickView(product)}
    >
      {/* Image */}
      <div className="relative h-44 bg-gradient-to-br from-purple-50 to-sky-50 flex items-center justify-center overflow-hidden">
        {product.images && product.images.length > 0 ? (
          <img
            src={product.images[0].image}
            alt={product.images[0].alt_text || product.name}
            loading="lazy"
            decoding="async"
            className="w-full h-full object-cover"
          />
        ) : (
          <CategoryIcon category={product.category?.name || null} />
        )}

        {/* Overlays */}
        {product.category && (
          <span className="absolute top-2 left-2 text-xs font-semibold px-2 py-0.5 rounded-full bg-sky-100 text-sky-700 border border-sky-200">
            {product.category.name}
          </span>
        )}
        <div className="absolute top-2 right-2">
          <StockBadge qty={product.stock_quantity} />
        </div>

        {/* Quick view hover overlay */}
        <div
          className="absolute inset-0 bg-purple-900/0 group-hover:bg-purple-900/10 transition-all duration-300 flex items-center justify-center opacity-0 group-hover:opacity-100 pointer-events-none"
        >
          <span className="flex items-center gap-1.5 bg-white text-purple-700 font-semibold text-xs px-3 py-1.5 rounded-full shadow border border-purple-100">
            <FiEye className="w-3.5 h-3.5" /> Quick View
          </span>
        </div>

        {product.featured && (
          <span className="absolute bottom-2 left-2 text-xs font-bold px-2 py-0.5 rounded-full bg-orange-500 text-white shadow">
            ★ Featured
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col flex-1">
        {product.brand && (
          <p className="text-xs text-gray-400 font-medium mb-0.5 uppercase tracking-wide">{product.brand}</p>
        )}
        <h3 className="font-bold text-purple-900 text-sm leading-snug line-clamp-2 mb-1">{product.name}</h3>
        {preview && (
          <p className="text-xs text-gray-500 line-clamp-2 mb-3 flex-1">{preview}</p>
        )}

        <div className="mt-auto">
          <div className="flex items-end justify-between mb-3">
            <div>
              <p className="text-xs text-gray-400">Price</p>
              <p className="text-xl font-extrabold text-orange-500">
                {product.currency} {isNaN(price) ? '—' : price.toFixed(2)}
              </p>
            </div>
          </div>

          <button
            onClick={(e) => { e.stopPropagation(); onAddToCart(product.id); }}
            disabled={product.stock_quantity === 0 || cartLoading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl font-bold text-sm transition disabled:cursor-not-allowed bg-orange-500 hover:bg-orange-600 text-white disabled:bg-gray-200 disabled:text-gray-400 shadow-sm"
          >
            <FiShoppingCart className="w-4 h-4" />
            {product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
          </button>
        </div>
      </div>
    </div>
  );
}
