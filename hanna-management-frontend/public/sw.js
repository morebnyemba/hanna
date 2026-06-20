/*
 * Hanna PWA service worker.
 * - App-shell style offline support with a versioned cache.
 * - Navigation requests: network-first, falling back to cache then /offline.
 * - Static assets (same-origin GET): stale-while-revalidate.
 * - API, auth and cross-origin requests are never cached.
 */
const CACHE_VERSION = 'v1';
const CACHE_NAME = `hanna-cache-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline.html';

const PRECACHE_URLS = [OFFLINE_URL, '/icons/icon.svg'];

// Paths that must always hit the network (never served from cache).
const NETWORK_ONLY_PREFIXES = ['/crm-api', '/api', '/auth'];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
        )
      )
      .then(() => self.clients.claim())
  );
});

function isNetworkOnly(url) {
  return NETWORK_ONLY_PREFIXES.some((prefix) => url.pathname.startsWith(prefix));
}

self.addEventListener('fetch', (event) => {
  const { request } = event;

  // Only handle same-origin GET requests; let everything else pass through.
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  if (isNetworkOnly(url)) return;

  // Navigations: network-first with offline fallback.
  if (request.mode === 'navigate') {
    event.respondWith(
      (async () => {
        try {
          const networkResponse = await fetch(request);
          const cache = await caches.open(CACHE_NAME);
          cache.put(request, networkResponse.clone());
          return networkResponse;
        } catch {
          const cached = await caches.match(request);
          return cached || (await caches.match(OFFLINE_URL));
        }
      })()
    );
    return;
  }

  // Static assets: stale-while-revalidate.
  event.respondWith(
    (async () => {
      const cache = await caches.open(CACHE_NAME);
      const cached = await cache.match(request);
      const networkFetch = fetch(request)
        .then((response) => {
          if (response && response.status === 200 && response.type === 'basic') {
            cache.put(request, response.clone());
          }
          return response;
        })
        .catch(() => cached);
      return cached || networkFetch;
    })()
  );
});
