// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

import { build, files, version } from "$service-worker";

const CACHE_KEY = `cache-${version}`;
const ASSETS = [...build, ...files];

self.addEventListener("install", (event) => {
  console.log("[Service Worker] Installing (caching application assets)");
  const cacheAssets = async () => {
    const cache = await caches.open(CACHE_KEY);
    await cache.addAll(ASSETS);
  };
  event.waitUntil(cacheAssets());
});


self.addEventListener("activate", (event) => {
  console.log("[Service Worker] Activating");
  const deleteOldCaches = async () => {
    for (const key of await caches.keys()) {
      if (key !== CACHE_KEY) {
        console.log(`[Service Worker] Deleting old cache: ${key}`);
        await caches.delete(key);
      }
    }
  };
  event.waitUntil(deleteOldCaches());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  // Serve application assets from cache, otherwise let the browser handle the request.
  if (!ASSETS.includes(url.pathname)) return;

  async function returnCachedAsset() {
    const cache = await caches.open(CACHE_KEY);
    console.debug(`[Service Worker] serving ${url.pathname} directly!`);
    return cache.match(event.request);
  }
  event.respondWith(returnCachedAsset());
});
