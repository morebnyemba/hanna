'use client';

import { useState, useEffect, useCallback } from 'react';

const KEY = 'hanna_wishlist_v1';

function load(): number[] {
  try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch { return []; }
}

function save(ids: number[]) {
  try { localStorage.setItem(KEY, JSON.stringify(ids)); } catch { /* best-effort */ }
}

export function useWishlist() {
  const [ids, setIds] = useState<number[]>([]);

  useEffect(() => { setIds(load()); }, []);

  const toggle = useCallback((id: number) => {
    setIds((prev) => {
      const next = prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id];
      save(next);
      return next;
    });
  }, []);

  const isWishlisted = useCallback((id: number) => ids.includes(id), [ids]);

  return { ids, toggle, isWishlisted };
}
