import type { OfflineBookEntry, OfflineBookPayload } from "@/lib/types";
import {
  OFFLINE_BOOKS_STORAGE_KEY,
  OFFLINE_BOOK_CACHE,
  OFFLINE_CHANGE_EVENT,
  buildOfflinePayloadCacheUrl,
  buildOfflineWarmUrls,
  resolveOfflineMode,
} from "@/lib/offlineUtils";

export function registerSW() {
  if (
    typeof window === "undefined" ||
    !("serviceWorker" in navigator) ||
    !("caches" in window)
  ) {
    return;
  }

  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

function getSWRegistration(): Promise<ServiceWorker | null> {
  return navigator.serviceWorker.ready.then((registration) => registration.active);
}

function readManifest(): OfflineBookEntry[] {
  if (typeof window === "undefined") return [];
  const stored = localStorage.getItem(OFFLINE_BOOKS_STORAGE_KEY);
  if (!stored) return [];

  try {
    const parsed = JSON.parse(stored);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeManifest(entries: OfflineBookEntry[]) {
  localStorage.setItem(OFFLINE_BOOKS_STORAGE_KEY, JSON.stringify(entries));
  window.dispatchEvent(new Event(OFFLINE_CHANGE_EVENT));
}

function markDownloaded(entry: OfflineBookEntry) {
  const existing = readManifest().filter((item) => item.bookId !== entry.bookId);
  existing.unshift(entry);
  writeManifest(existing);
}

function unmarkDownloaded(bookId: string) {
  writeManifest(readManifest().filter((entry) => entry.bookId !== bookId));
}

async function putOfflinePayload(payload: OfflineBookPayload) {
  const cache = await caches.open(OFFLINE_BOOK_CACHE);
  const response = new Response(JSON.stringify(payload), {
    headers: { "Content-Type": "application/json" },
  });
  await cache.put(buildOfflinePayloadCacheUrl(payload.bookId), response);
}

async function deleteOfflinePayload(bookId: string) {
  if (typeof window === "undefined" || !("caches" in window)) return;
  const cache = await caches.open(OFFLINE_BOOK_CACHE);
  await cache.delete(buildOfflinePayloadCacheUrl(bookId));
}

async function warmRoute(url: string): Promise<void> {
  if (typeof document === "undefined") return;

  await new Promise<void>((resolve) => {
    const iframe = document.createElement("iframe");
    iframe.src = url;
    iframe.setAttribute("aria-hidden", "true");
    iframe.style.position = "absolute";
    iframe.style.width = "1px";
    iframe.style.height = "1px";
    iframe.style.opacity = "0";
    iframe.style.pointerEvents = "none";
    iframe.style.left = "-9999px";

    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      iframe.remove();
      resolve();
    };

    iframe.onload = finish;
    iframe.onerror = finish;
    setTimeout(finish, 5000);

    document.body.appendChild(iframe);
  });
}

async function warmOfflinePages(bookId: string) {
  for (const url of buildOfflineWarmUrls(bookId)) {
    await warmRoute(url);
  }
}

function buildManifestEntry(payload: OfflineBookPayload): OfflineBookEntry {
  return {
    bookId: payload.bookId,
    title: payload.title,
    authorName: payload.authorName,
    coverImage: payload.coverImage,
    accentColor: payload.accentColor,
    totalChapters: payload.totalChapters,
    mode: payload.mode,
    languageParam: payload.languageParam,
    cachedAt: new Date().toISOString(),
    estimatedSizeMB: payload.estimatedSizeMB,
  };
}

export function getDownloadedBooks(): OfflineBookEntry[] {
  return readManifest();
}

export function getDownloadedBook(bookId: string): OfflineBookEntry | null {
  return readManifest().find((entry) => entry.bookId === bookId) ?? null;
}

export function isDownloaded(bookId: string, languageParam?: string): boolean {
  const entry = getDownloadedBook(bookId);
  if (!entry) return false;

  const requestedMode = resolveOfflineMode(languageParam);
  return entry.mode === requestedMode && entry.languageParam === languageParam;
}

export function subscribeOfflineBooks(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};

  const handler = () => callback();
  window.addEventListener(OFFLINE_CHANGE_EVENT, handler);
  window.addEventListener("storage", handler);
  return () => {
    window.removeEventListener(OFFLINE_CHANGE_EVENT, handler);
    window.removeEventListener("storage", handler);
  };
}

export async function loadOfflinePayload(bookId: string): Promise<OfflineBookPayload | null> {
  if (typeof window === "undefined" || !("caches" in window)) return null;
  const cache = await caches.open(OFFLINE_BOOK_CACHE);
  const response = await cache.match(buildOfflinePayloadCacheUrl(bookId));
  if (!response) return null;
  return response.json();
}

export async function downloadBook(
  bookId: string,
  languageParam: string | undefined,
  onProgress: (percent: number) => void,
): Promise<void> {
  const worker = await getSWRegistration();
  if (!worker) throw new Error("Service worker not available");

  const search = languageParam
    ? `?language=${encodeURIComponent(languageParam)}`
    : "";
  const response = await fetch(`/api/offline/books/${bookId}${search}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch offline payload (${response.status})`);
  }

  const payload = (await response.json()) as OfflineBookPayload;
  await putOfflinePayload(payload);

  return new Promise((resolve, reject) => {
    let settled = false;
    const finishResolve = () => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      resolve();
    };
    const finishReject = (error: Error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      unmarkDownloaded(bookId);
      void deleteOfflinePayload(bookId).finally(() => reject(error));
    };

    const handler = async (event: MessageEvent) => {
      const data = event.data;
      if (!data || data.bookId !== bookId) return;

      if (data.type === "PROGRESS") {
        onProgress(Math.round((data.done / data.total) * 100));
      }

      if (data.type === "COMPLETE") {
        navigator.serviceWorker.removeEventListener("message", handler);
        try {
          await warmOfflinePages(bookId);
          markDownloaded(buildManifestEntry(payload));
          finishResolve();
        } catch (error) {
          finishReject(error instanceof Error ? error : new Error("Failed to warm offline pages"));
        }
      }

      if (data.type === "ERROR") {
        navigator.serviceWorker.removeEventListener("message", handler);
        finishReject(new Error(data.message || "Offline download failed"));
      }
    };

    navigator.serviceWorker.addEventListener("message", handler);

    const timeout = setTimeout(() => {
      navigator.serviceWorker.removeEventListener("message", handler);
      finishReject(new Error("Download timed out"));
    }, 5 * 60 * 1000);

    worker.postMessage({
      type: "CACHE_BOOK",
      bookId,
      payload,
      cacheKey: buildOfflinePayloadCacheUrl(bookId),
    });
  });
}

export async function removeBook(bookId: string): Promise<void> {
  const worker = await getSWRegistration();
  if (!worker) {
    await deleteOfflinePayload(bookId);
    unmarkDownloaded(bookId);
    return;
  }

  const payload = await loadOfflinePayload(bookId);

  return new Promise((resolve) => {
    const finalize = async () => {
      clearTimeout(timeout);
      navigator.serviceWorker.removeEventListener("message", handler);
      await deleteOfflinePayload(bookId);
      unmarkDownloaded(bookId);
      resolve();
    };

    const handler = (event: MessageEvent) => {
      if (event.data.type === "DELETED" && event.data.bookId === bookId) {
        void finalize();
      }
    };

    navigator.serviceWorker.addEventListener("message", handler);
    const timeout = setTimeout(() => {
      void finalize();
    }, 15_000);

    worker.postMessage({
      type: "DELETE_BOOK",
      bookId,
      payload,
      cacheKey: buildOfflinePayloadCacheUrl(bookId),
    });
  });
}
