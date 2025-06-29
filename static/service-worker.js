const CACHE_NAME = 'flowers-cache-v1';
const urlsToCache = [
  '/',
  '/static/css/custom.css',
  '/static/images/logo.png',
  '/manifest.json',  // <- use the correct path here
  // Add other important files
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request);
    }).catch(() => {
      if (event.request.mode === 'navigate') {
        return caches.match('/');
      }
    })
  );
});
