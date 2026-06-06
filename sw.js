// ─────────────────────────────────────────────────────────────────
//  Signal PWA · Service Worker v3
//  Bump CACHE_VER setiap kali deploy file baru agar homescreen
//  tidak pakai stale cache lama.
// ─────────────────────────────────────────────────────────────────
const CACHE_VER = 'signal-v3';
const STATIC_ASSETS = [
  './index.html',
  './manifest.json',
];

// Semua domain API yang harus network-first (jangan pernah di-cache)
const API_HOSTS = [
  'api.binance.com',
  'api.bybit.com',
  'api.gateio.ws',
  'api.coingecko.com',
  'open.er-api.com',
  'api.exchangerate.host',
  'fonts.googleapis.com',
  'fonts.gstatic.com',
];

function isApiRequest(url) {
  return API_HOSTS.some(host => url.includes(host));
}

// ── INSTALL ───────────────────────────────────────────────────────
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_VER)
      .then(cache => cache.addAll(STATIC_ASSETS))
      .then(() => self.skipWaiting())
  );
});

// ── ACTIVATE ──────────────────────────────────────────────────────
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys
          .filter(k => k !== CACHE_VER)
          .map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── FETCH ─────────────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  const url = e.request.url;

  // API calls → selalu network-first, jangan cache
  if (isApiRequest(url)) {
    e.respondWith(
      fetch(e.request, { cache: 'no-store' }).catch(() =>
        new Response(
          JSON.stringify({ error: 'offline', ts: Date.now() }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        )
      )
    );
    return;
  }

  // Static assets → cache-first, fallback ke network
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(response => {
        // Hanya cache GET requests yang sukses
        if (
          e.request.method === 'GET' &&
          response.status === 200 &&
          response.type !== 'opaque'
        ) {
          const clone = response.clone();
          caches.open(CACHE_VER).then(cache => cache.put(e.request, clone));
        }
        return response;
      }).catch(() => {
        // Offline fallback: kembalikan index.html untuk navigasi
        if (e.request.mode === 'navigate') {
          return caches.match('./index.html');
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});
