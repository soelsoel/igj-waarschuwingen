const CACHE = 'igj-v2';
const SHELL = [
    './',
    './index.html',
    './app.js',
    './data/warnings.json',
    './static/manifest.json',
    './static/icon-192.svg',
    './static/icon-512.svg',
];
const TAILWIND = 'https://cdn.tailwindcss.com';

self.addEventListener('install', (event) => {
    event.waitUntil((async () => {
        const cache = await caches.open(CACHE);
        await cache.addAll(SHELL);
        // cache.add() rejects opaque responses, so fetch and put the CDN script by hand.
        const request = new Request(TAILWIND, { mode: 'no-cors' });
        await fetch(request).then((res) => cache.put(request, res)).catch(() => {});
        self.skipWaiting();
    })());
});

self.addEventListener('activate', (event) => {
    event.waitUntil((async () => {
        const keys = await caches.keys();
        await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
        self.clients.claim();
    })());
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    if (request.method !== 'GET') return;

    // Data: fresh when online, cached copy when offline.
    if (new URL(request.url).pathname.endsWith('/data/warnings.json')) {
        event.respondWith((async () => {
            try {
                const response = await fetch(request);
                const cache = await caches.open(CACHE);
                cache.put('./data/warnings.json', response.clone());
                return response;
            } catch (error) {
                const cached = await caches.match('./data/warnings.json');
                if (cached) return cached;
                throw error;
            }
        })());
        return;
    }

    if (request.mode === 'navigate') {
        event.respondWith(fetch(request).catch(() => caches.match('./index.html')));
        return;
    }

    event.respondWith(caches.match(request).then((cached) => cached || fetch(request)));
});
