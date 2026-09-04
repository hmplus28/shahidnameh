const CACHE_NAME = 'shahidnameh-v8';
const APP_SHELL = [
  '/', '/martyrs/', '/offline/',
  '/static/css/site.css', '/static/css/fonts.css',
  '/static/fonts/vazirmatn-arabic.woff2', '/static/fonts/vazirmatn-latin.woff2', '/static/fonts/vazirmatn-latin-ext.woff2',
  '/static/js/site.js', '/static/manifest.webmanifest',
  '/static/icons/icon.svg', '/static/icons/icon-maskable.svg',
  '/static/icons/tulip.svg', '/static/icons/crescent-star.svg', '/static/icons/mosque.svg',
  '/static/icons/kafiyeh.svg', '/static/icons/medal.svg', '/static/icons/testament.svg',
  '/static/icons/red-crescent.svg', '/static/icons/star-islamic.svg',
  '/static/icons/home.svg', '/static/icons/search.svg', '/static/icons/offline.svg',
  '/static/icons/menu.svg', '/static/icons/install.svg', '/static/icons/play.svg',
  '/static/icons/external.svg', '/static/icons/arrow-left.svg', '/static/icons/arrow-right.svg',
  '/static/icons/page.svg', '/static/icons/plus.svg', '/static/icons/clock.svg',
  '/static/icons/users.svg', '/static/icons/dashboard.svg', '/static/icons/logout.svg',
  '/static/icons/close.svg', '/static/icons/mihrab.svg', '/static/icons/empty.svg',
  '/static/icons/default-avatar.svg', '/static/icons/city-silhouette.svg',
  '/static/images/hero/home-hero.jpg', '/static/images/hero/memories-bg.jpg',
  '/static/images/hero/directory-hero.jpg', '/static/images/hero/offline-bg.jpg',
  '/static/images/hero/front-bg.jpg', '/static/images/hero/testament-bg.jpg',
  '/static/images/hero/hero-banner.jpg', '/static/images/hero/city-silhouette-bg.jpg',
  '/static/images/leaders/khomeini-portrait.jpg', '/static/images/leaders/khamenei-portrait.jpg',
  '/static/images/leaders/khomeini-wide.jpg', '/static/images/leaders/khamenei-wide.jpg',
  '/static/images/default-avatar.png'
];

const isCacheable = (request, response) => request.method === 'GET' && response && response.ok && new URL(request.url).origin === self.location.origin;
const putInCache = async (request, response) => {
  if (!isCacheable(request, response)) return response;
  const cache = await caches.open(CACHE_NAME);
  await cache.put(request, response.clone());
  return response;
};

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL).catch((err) => console.warn('Cache addAll partial fail:', err))).then(() => self.skipWaiting()));
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
