'use client';

import { useState, useEffect } from 'react';
import { FiX, FiZap } from 'react-icons/fi';

const DISMISS_KEY = 'hanna_announcement_dismissed_v1';

interface AnnouncementBarProps {
  message?: string;
  ctaLabel?: string;
  ctaHref?: string;
}

export default function AnnouncementBar({
  message = '🎉 Free delivery on orders over $300 · Solar systems from $499 · Starlink kits in stock now',
  ctaLabel = 'Shop Now',
  ctaHref = '#product-section',
}: AnnouncementBarProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      if (!sessionStorage.getItem(DISMISS_KEY)) setVisible(true);
    } catch { setVisible(true); }
  }, []);

  const dismiss = () => {
    setVisible(false);
    try { sessionStorage.setItem(DISMISS_KEY, '1'); } catch { /* best-effort */ }
  };

  if (!visible) return null;

  return (
    <div className="bg-gradient-to-r from-sky-700 via-sky-600 to-blue-700 text-white text-xs sm:text-sm font-semibold">
      <div className="max-w-7xl mx-auto px-4 py-2.5 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <FiZap className="w-3.5 h-3.5 flex-shrink-0 text-orange-300" />
          <p className="truncate">{message}</p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <a
            href={ctaHref}
            className="hidden sm:inline-flex items-center px-3 py-1 bg-white/20 hover:bg-white/30 rounded-full text-white text-xs font-bold transition"
          >
            {ctaLabel}
          </a>
          <button onClick={dismiss} className="p-1 hover:bg-white/20 rounded-full transition" aria-label="Dismiss">
            <FiX className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
