'use client';

import { useEffect } from 'react';

/**
 * Registers the PWA service worker on the client.
 * Registration is skipped in development to avoid stale caches while iterating.
 */
export default function ServiceWorkerRegistration() {
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (!('serviceWorker' in navigator)) return;
    if (process.env.NODE_ENV !== 'production') return;

    const register = () => {
      navigator.serviceWorker
        .register('/sw.js', { scope: '/' })
        .catch((err) => {
          // Non-fatal: the app still works without offline support.
          console.warn('[pwa] Service worker registration failed:', err);
        });
    };

    if (document.readyState === 'complete') {
      register();
    } else {
      window.addEventListener('load', register);
      return () => window.removeEventListener('load', register);
    }
  }, []);

  return null;
}
