'use client';

import { FiHeart } from 'react-icons/fi';

interface WishlistButtonProps {
  productId: number;
  isWishlisted: boolean;
  onToggle: (id: number) => void;
  size?: 'sm' | 'md';
}

export default function WishlistButton({ productId, isWishlisted, onToggle, size = 'sm' }: WishlistButtonProps) {
  const sz = size === 'sm' ? 'w-7 h-7' : 'w-9 h-9';
  const icon = size === 'sm' ? 'w-3.5 h-3.5' : 'w-4.5 h-4.5';
  return (
    <button
      onClick={(e) => { e.stopPropagation(); onToggle(productId); }}
      aria-label={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
      className={`${sz} rounded-full flex items-center justify-center transition-all shadow-sm border ${
        isWishlisted
          ? 'bg-red-500 border-red-500 text-white scale-110'
          : 'bg-white border-gray-200 text-gray-400 hover:border-red-300 hover:text-red-400'
      }`}
    >
      <FiHeart className={`${icon} ${isWishlisted ? 'fill-current' : ''}`} />
    </button>
  );
}
