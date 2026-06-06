// ─────────────────────────────────────────────────────────────────
//  Signal PWA · Service Worker v4
//  - Network-first untuk semua API (Binance, Gate, Bybit, CoinGecko)
//  - Push notification handler (saat app di background)
//  - postMessage handler untuk audio relay
// ─────────────────────────────────────────────────────────────────
const CACHE_VER = 'signal-v4';
const STATIC_ASSETS = [
  './index.html',
  './manifest.json',
];

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
        keys.filter(k => k !== CACHE_VER).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

// ── FETCH ─────────────────────────────────────────────────────────
self.addEventListener('fetch', e => {
  const url = e.request.url;
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
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(response => {
        if (e.request.method === 'GET' && response.status === 200 && response.type !== 'opaque') {
          const clone = response.clone();
          caches.open(CACHE_VER).then(cache => cache.put(e.request, clone));
        }
        return response;
      }).catch(() => {
        if (e.request.mode === 'navigate') return caches.match('./index.html');
        return new Response('Offline', { status: 503 });
      });
    })
  );
});

// ── PUSH NOTIFICATION (dari server atau self.registration.showNotification) ──
self.addEventListener('push', e => {
  let data = { title: '🔔 Signal Alert', body: 'Sinyal berubah!', action: 'HOLD' };
  try { data = e.data.json(); } catch(err) {}

  const emoji = data.action==='BUY'?'🟢':data.action==='SELL'?'🔴':'🟡';
  e.waitUntil(
    self.registration.showNotification(`${emoji} ${data.title}`, {
      body: data.body,
      icon: './icon-192.png',
      badge: './icon-192.png',
      tag: 'signal-alert',
      renotify: true,
      vibrate: data.action==='BUY' ? [100,50,100,50,200] :
               data.action==='SELL'? [300,100,300] : [150,100,150],
      data: data,
    })
  );
});

// ── NOTIF CLICK ───────────────────────────────────────────────────
self.addEventListener('notificationclick', e => {
  e.notification.close();
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(cs => {
      if (cs.length > 0) { cs[0].focus(); return; }
      return clients.openWindow('./index.html');
    })
  );
});

// ── MESSAGE FROM APP → kirim notif background ─────────────────────
// App mengirim { type:'SIGNAL_ALERT', title, body, action } via postMessage
// SW akan showNotification sehingga muncul meski app di background
self.addEventListener('message', e => {
  if (!e.data || e.data.type !== 'SIGNAL_ALERT') return;
  const d = e.data;
  const emoji = d.action==='BUY'?'🟢':d.action==='SELL'?'🔴':'🟡';
  self.registration.showNotification(`${emoji} ${d.title}`, {
    body: d.body,
    icon: './icon-192.png',
    badge: './icon-192.png',
    tag: 'signal-alert',
    renotify: true,
    vibrate: d.action==='BUY' ? [100,50,100,50,200] :
             d.action==='SELL'? [300,100,300] : [150,100,150],
    data: d,
  });
});
