import type { Chapter, OfflineMode } from "./types";

export const OFFLINE_BOOKS_STORAGE_KEY = "offline-books-manifest-v1";
export const OFFLINE_BOOK_CACHE = "offline-books-v1";
export const OFFLINE_CHANGE_EVENT = "offline-books-changed";
export const OFFLINE_UNAVAILABLE_URL = "/offline-unavailable";

export function resolveOfflineMode(languageParam?: string): OfflineMode {
  if (!languageParam) return "english";
  if (languageParam === "modern") return "modern";
  if (languageParam === "child") return "child";
  return "original";
}

export function describeOfflineMode(mode: OfflineMode, languageParam?: string): string {
  if (mode === "original" && languageParam) {
    return `Original (${languageParam})`;
  }
  return mode[0].toUpperCase() + mode.slice(1);
}

export function buildOfflinePayloadCacheUrl(bookId: string): string {
  return `/__offline/books/${bookId}.json`;
}

export function buildOfflineBookUrl(bookId: string): string {
  return `/offline/books/${bookId}`;
}

export function buildOfflineGlossaryUrl(bookId: string, search = ""): string {
  const normalizedSearch = search && !search.startsWith("?") ? `?${search}` : search;
  return `/offline/books/${bookId}/glossary${normalizedSearch}`;
}

export function buildOfflineReadUrl(bookId: string, target?: string): string {
  if (!target) return `/offline/read/${bookId}`;
  return `/offline/read/${bookId}?target=${encodeURIComponent(target)}`;
}

export function buildOfflineWarmUrls(bookId: string): string[] {
  return [
    "/downloads",
    OFFLINE_UNAVAILABLE_URL,
    buildOfflineBookUrl(bookId),
    buildOfflineGlossaryUrl(bookId),
    buildOfflineReadUrl(bookId),
  ];
}

export function resolveOfflineNavigationTarget(pathname: string, search = ""): string | null {
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

export function buildOfflineCacheLookupUrls(url: string): string[] {
  const [pathname] = url.split("?");
  if (pathname !== url && pathname.startsWith("/offline/")) {
    return [url, pathname];
  }
  return [url];
}

export function resolveOfflineTargetChapterIndex(chapters: Chapter[], target?: string | null): number {
  if (!target) return 0;

  const path = target.replace(/^\/+|\/+$/g, "");
  if (!path) return 0;

  const segments = path.split("/").filter(Boolean);

  if (segments.length === 1 || segments.length === 2) {
    const num = parseInt(segments[0], 10);
    if (!Number.isFinite(num)) return 0;
    return Math.max(0, Math.min(num - 1, chapters.length - 1));
  }

  if (segments.length >= 4) {
    const partNum = parseInt(segments[0], 10);
    const chapterNum = parseInt(segments[2], 10);
    const idx = chapters.findIndex(
      (chapter) => chapter.part === partNum && chapter.number === chapterNum,
    );
    return idx >= 0 ? idx : 0;
  }

  return 0;
}
