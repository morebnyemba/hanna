'use client';

import { useState, useEffect, useCallback } from 'react';
import type { Product } from '../_components/ProductCard';

const KEY = 'hanna_recently_viewed_v1';
const MAX = 10;

function load(): Product[] {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; }
}

function save(products: Product[]) {
  try { localStorage.setItem(KEY, JSON.stringify(products)); } catch { /* best-effort */ }
}

export function useRecentlyViewed() {
  const [viewed, setViewed] = useState<Product[]>([]);

  useEffect(() => { setViewed(load()); }, []);

  const track = useCallback((product: Product) => {
    setViewed((prev) => {
      const deduped = [product, ...prev.filter((p) => p.id !== product.id)].slice(0, MAX);
      save(deduped);
      return deduped;
    });
  }, []);

  return { viewed, track };
}
