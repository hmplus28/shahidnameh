const CACHE_NAME = 'shahidnameh-v6';
const APP_SHELL = ['/', '/martyrs/', '/offline/', '/static/css/site.css', '/static/css/fonts.css', '/static/fonts/vazirmatn-arabic.woff2', '/static/fonts/vazirmatn-latin.woff2', '/static/fonts/vazirmatn-latin-ext.woff2', '/static/js/site.js', '/static/manifest.webmanifest', '/static/icons/icon.svg', '/static/icons/icon-maskable.svg', '/static/images/hero-banner.jpg', '/static/images/memories-bg.jpg', '/static/images/offline-bg.jpg', '/static/images/directory-hero.jpg', '/static/images/front-bg.jpg', '/static/images/testament-bg.jpg', '/static/images/city-silhouette.png', '/static/images/default-avatar.png'];

const isCacheable = (request, response) => request.method === 'GET' && response && response.ok && new URL(request.url).origin === self.location.origin;
const putInCache = async (request, response) => {
  if (!isCacheable(request, response)) return response;
  const cache = await caches.open(CACHE_NAME);
  await cache.put(request, response.clone());
  return response;
};

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') self.skipWaiting();
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).then((response) => putInCache(request, response)).catch(async () => (await caches.match(request)) || (await caches.match('/offline/'))));
    return;
  }
  if (new URL(request.url).origin !== self.location.origin) return;
  event.respondWith(
    caches.match(request).then((cached) => {
      const network = fetch(request)
        .then((response) => {
          if (isCacheable(request, response)) putInCache(request, response);
          return response;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
