"use client";

import type { ReadingProgress } from "./types";
import type { CloudUserData, CloudReaderPrefs } from "./firestore";

type ProgressMap = Record<string, ReadingProgress>;
type LanguageMap = Record<string, string>;

let debounceTimer: ReturnType<typeof setTimeout> | null = null;
const DEBOUNCE_MS = 5000;

export async function fetchFromCloud(): Promise<CloudUserData | null> {
  try {
    const res = await fetch("/api/reading-sync");
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export function syncToCloud(
  progress: ProgressMap,
  languages: LanguageMap,
  readerPrefs?: CloudReaderPrefs
) {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetch("/api/reading-sync", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ progress, languages, readerPrefs }),
    }).catch(() => {
      // Silent fail — will retry on next change
    });
  }, DEBOUNCE_MS);
}

export function flushViaBeacon(
  progress: ProgressMap,
  languages: LanguageMap,
  readerPrefs?: CloudReaderPrefs
) {
  const payload = JSON.stringify({ progress, languages, readerPrefs });
  navigator.sendBeacon("/api/reading-sync", new Blob([payload], { type: "application/json" }));
}

/**
 * Per-book last-write-wins merge.
 * Returns merged progress and languages.
 */
export function mergeState(
  local: { progress: ProgressMap; languages: LanguageMap },
  cloud: { progress: ProgressMap; languages: LanguageMap }
): { progress: ProgressMap; languages: LanguageMap } {
  const mergedProgress: ProgressMap = { ...cloud.progress };
  for (const [bookId, localEntry] of Object.entries(local.progress)) {
    const cloudEntry = cloud.progress[bookId];
    if (
      !cloudEntry ||
      new Date(localEntry.lastReadAt) >= new Date(cloudEntry.lastReadAt)
    ) {
      mergedProgress[bookId] = localEntry;
    }
  }

  const mergedLanguages: LanguageMap = { ...cloud.languages };
  // Local languages override cloud for books with more recent local progress
  for (const bookId of Object.keys(local.languages)) {
    const localProgress = local.progress[bookId];
    const cloudProgress = cloud.progress[bookId];
    if (
      !cloudProgress ||
      (localProgress &&
        new Date(localProgress.lastReadAt) >=
          new Date(cloudProgress.lastReadAt))
    ) {
      mergedLanguages[bookId] = local.languages[bookId];
    }
  }

  return { progress: mergedProgress, languages: mergedLanguages };
}
