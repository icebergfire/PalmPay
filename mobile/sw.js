// PalmPay Service Worker v1.0
// Caches app shell + ML models for offline use

const CACHE_NAME = 'palmpay-v2';
const CACHE_ML   = 'palmpay-ml-v2';

// App shell — cache immediately
const SHELL_FILES = [
  './palmpay.html',
  './manifest.json',
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap'
];

// ML libs — cache on first use (large files, cache separately)
const ML_URLS = [
  'https://cdn.jsdelivr.net/npm/@mediapipe/hands@0.4.1646424915/hands.js',
  'https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.17.0/dist/tf.min.js',
  'https://cdn.jsdelivr.net/npm/@tensorflow-models/mobilenet@2.1.1/dist/mobilenet.min.js'
];

// ── Install: cache app shell ──
self.addEventListener('install', event => {
  console.log('[SW] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(SHELL_FILES.filter(u => !u.startsWith('http') || u.includes('fonts'))))
      .then(() => self.skipWaiting())
      .catch(e => console.warn('[SW] Shell cache failed:', e))
  );
});

// ── Activate: clean old caches ──
self.addEventListener('activate', event => {
  console.log('[SW] Activating...');
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(k => k !== CACHE_NAME && k !== CACHE_ML)
          .map(k => { console.log('[SW] Removing old cache:', k); return caches.delete(k); })
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: serve from cache, fallback to network ──
self.addEventListener('fetch', event => {
  const url = event.request.url;

  // Skip non-GET and cross-origin non-CDN requests
  if (event.request.method !== 'GET') return;

  // ML libs — cache-first with long TTL
  if (ML_URLS.some(ml => url.includes(ml.split('/').slice(-1)[0].split('@')[0]) ||
      url.includes('mediapipe') || url.includes('tensorflow') || url.includes('mobilenet'))) {
    event.respondWith(
      caches.open(CACHE_ML).then(async cache => {
        const cached = await cache.match(event.request);
        if (cached) return cached;
        try {
          const resp = await fetch(event.request);
          if (resp.ok) cache.put(event.request, resp.clone());
          return resp;
        } catch(e) {
          console.warn('[SW] ML fetch failed:', url);
          throw e;
        }
      })
    );
    return;
  }

  // App shell + fonts — network-first with cache fallback
  event.respondWith(
    fetch(event.request)
      .then(resp => {
        if (resp.ok && (url.endsWith('.html') || url.endsWith('.json') || url.includes('fonts'))) {
          const clone = resp.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return resp;
      })
      .catch(() => caches.match(event.request))
  );
});
