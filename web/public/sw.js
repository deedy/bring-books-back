const STATIC_CACHE = "offline-static-v1";
const BOOK_CACHE = "offline-books-v1";
const RUNTIME_CACHE = "offline-runtime-v1";
const OFFLINE_UNAVAILABLE_URL = "/offline-unavailable";

const PRECACHE_URLS = [
  "/downloads",
  OFFLINE_UNAVAILABLE_URL,
  "/manifest.json",
  "/favicon.ico",
  "/favicon.png",
  "/logo.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((cache) => cache.addAll(PRECACHE_URLS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

function buildOfflineBookUrl(bookId) {
  return `/offline/books/${bookId}`;
}

function buildOfflineGlossaryUrl(bookId, search = "") {
  const normalizedSearch = search && !search.startsWith("?") ? `?${search}` : search;
  return `/offline/books/${bookId}/glossary${normalizedSearch}`;
}

function buildOfflineReadUrl(bookId, target) {
  if (!target) return `/offline/read/${bookId}`;
  return `/offline/read/${bookId}?target=${encodeURIComponent(target)}`;
}

function buildOfflineWarmUrls(bookId) {
  return [
    "/downloads",
    OFFLINE_UNAVAILABLE_URL,
    buildOfflineBookUrl(bookId),
    buildOfflineGlossaryUrl(bookId),
    buildOfflineReadUrl(bookId),
  ];
}

function buildPayloadCacheUrl(bookId) {
  return `/__offline/books/${bookId}.json`;
}

function resolveOfflineNavigationTarget(pathname, search = "") {
  const normalizedSearch = search && !search.startsWith("?") ? `?${search}` : search;

  if (
    pathname === "/downloads" ||
    pathname === OFFLINE_UNAVAILABLE_URL ||
    pathname.startsWith("/offline/")
  ) {
    return `${pathname}${normalizedSearch}`;
  }

  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] === "books" && segments[1]) {
    if (segments[2] === "glossary") {
      return buildOfflineGlossaryUrl(segments[1], normalizedSearch);
    }
    return buildOfflineBookUrl(segments[1]);
  }

  if (segments[0] === "read" && segments[1]) {
    const target = segments.slice(2).join("/");
    return buildOfflineReadUrl(segments[1], target || undefined);
  }

  return null;
}

function buildOfflineCacheLookupUrls(url) {
  const [pathname] = url.split("?");
  if (pathname !== url && pathname.startsWith("/offline/")) {
    return [url, pathname];
  }
  return [url];
}

async function postMessage(clientId, data) {
  if (!clientId) return;
  const client = await self.clients.get(clientId);
  if (client) {
    client.postMessage(data);
  }
}

async function cacheResponse(cache, requestUrl, response) {
  if (response && response.ok) {
    await cache.put(requestUrl, response.clone());
  }
}

async function fetchAndCache(cache, requestUrl) {
  const response = await fetch(requestUrl, { credentials: "same-origin" });
  await cacheResponse(cache, requestUrl, response);
}

self.addEventListener("message", (event) => {
  const data = event.data || {};
  const clientId = event.source && "id" in event.source ? event.source.id : null;

  if (data.type === "CACHE_BOOK") {
    event.waitUntil(
      (async () => {
        try {
          const cache = await caches.open(BOOK_CACHE);
          const urls = Array.from(
            new Set([...(data.payload?.assetUrls || []), ...buildOfflineWarmUrls(data.bookId)])
          );
          const total = urls.length + 1;
          let done = 0;

          await cache.put(
            data.cacheKey || buildPayloadCacheUrl(data.bookId),
            new Response(JSON.stringify(data.payload), {
              headers: { "Content-Type": "application/json" },
            })
          );
          done += 1;
          await postMessage(clientId, { type: "PROGRESS", bookId: data.bookId, done, total });

          for (const url of urls) {
            try {
              await fetchAndCache(cache, url);
            } catch {
              // Ignore individual asset failures; the payload itself is still cached.
            }
            done += 1;
            await postMessage(clientId, { type: "PROGRESS", bookId: data.bookId, done, total });
          }

          await postMessage(clientId, { type: "COMPLETE", bookId: data.bookId });
        } catch (error) {
          await postMessage(clientId, {
            type: "ERROR",
            bookId: data.bookId,
            message: error instanceof Error ? error.message : "Unknown error",
          });
        }
      })()
    );
  }

  if (data.type === "DELETE_BOOK") {
    event.waitUntil(
      (async () => {
        const cache = await caches.open(BOOK_CACHE);
        const urls = Array.from(
          new Set([
            data.cacheKey || buildPayloadCacheUrl(data.bookId),
            ...((data.payload && data.payload.assetUrls) || []),
            ...buildOfflineWarmUrls(data.bookId),
          ])
        );

        await Promise.all(urls.map((url) => cache.delete(url)));
        await postMessage(clientId, { type: "DELETED", bookId: data.bookId });
      })()
    );
  }
});

async function cacheFirst(request) {
  const cached = await caches.match(request);
  if (cached) return cached;

  const response = await fetch(request);
  const cache = await caches.open(RUNTIME_CACHE);
  await cacheResponse(cache, request, response);
  return response;
}

async function hasOfflineBook(bookId) {
  const cached = await caches.match(buildPayloadCacheUrl(bookId));
  return !!cached;
}

async function findCachedOfflineResponse(target) {
  for (const cacheKey of buildOfflineCacheLookupUrls(target)) {
    const cached = await caches.match(cacheKey);
    if (cached) return cached;
  }
  return null;
}

async function offlineNavigationTarget(url) {
  const pathParts = url.pathname.split("/").filter(Boolean);

  if (url.pathname === "/downloads" || url.pathname === OFFLINE_UNAVAILABLE_URL || url.pathname.startsWith("/offline/")) {
    return resolveOfflineNavigationTarget(url.pathname, url.search);
  }

  if ((pathParts[0] === "books" || pathParts[0] === "read") && pathParts[1] && !(await hasOfflineBook(pathParts[1]))) {
    return null;
  }

  return resolveOfflineNavigationTarget(url.pathname, url.search);
}

async function handleNavigation(request) {
  try {
    const networkRequest = new Request(request, { cache: "no-store" });
    const response = await fetch(networkRequest);
    const cache = await caches.open(RUNTIME_CACHE);
    await cacheResponse(cache, request, response);
    return response;
  } catch {
    const url = new URL(request.url);
    const target = await offlineNavigationTarget(url);
    if (target) {
      const cached = await findCachedOfflineResponse(target);
      if (cached) {
        const isOfflineRoute =
          url.pathname === "/downloads" ||
          url.pathname === OFFLINE_UNAVAILABLE_URL ||
          url.pathname.startsWith("/offline/");

        if (isOfflineRoute) return cached;
        return Response.redirect(new URL(target, url.origin).toString(), 302);
      }
    }

    const fallback = await caches.match(OFFLINE_UNAVAILABLE_URL);
    if (fallback) return fallback;

    return new Response("Offline", {
      status: 503,
      headers: { "Content-Type": "text/plain; charset=utf-8" },
    });
  }
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  if (request.method !== "GET" || url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(handleNavigation(request));
    return;
  }

  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.startsWith("/data/") ||
    url.pathname.startsWith("/offline/") ||
    url.pathname === "/downloads" ||
    url.pathname === "/manifest.json" ||
    url.pathname === "/favicon.ico" ||
    url.pathname === "/favicon.png" ||
    url.pathname === "/logo.png"
  ) {
    event.respondWith(cacheFirst(request));
  }
});
