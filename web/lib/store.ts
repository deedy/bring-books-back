"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ReadingProgress } from "./types";

export interface ReaderPreferences {
  darkMode: boolean;
  fontSize: "small" | "medium" | "large";
}

interface ReadingStore {
  progress: Record<string, ReadingProgress>;
  scrollMode: "paginated" | "infinite";
  bookLanguages: Record<string, string>;
  readerPrefs: ReaderPreferences;
  updateProgress: (bookId: string, progress: Partial<ReadingProgress>) => void;
  getProgress: (bookId: string) => ReadingProgress | null;
  markFinished: (bookId: string) => void;
  setScrollMode: (mode: "paginated" | "infinite") => void;
  setBookLanguage: (bookId: string, language: string | undefined) => void;
  getBookLanguage: (bookId: string) => string | undefined;
  setReaderPrefs: (prefs: Partial<ReaderPreferences>) => void;
  mergeFromCloud: (
    cloudProgress: Record<string, ReadingProgress>,
    cloudLanguages: Record<string, string>,
    cloudPrefs?: ReaderPreferences
  ) => void;
}

export const useReadingStore = create<ReadingStore>()(
  persist(
    (set, get) => ({
      progress: {},
      scrollMode: "paginated" as "paginated" | "infinite",
      bookLanguages: {},
      readerPrefs: { darkMode: true, fontSize: "medium" } as ReaderPreferences,
      setScrollMode: (mode: "paginated" | "infinite") => set({ scrollMode: mode }),
      setBookLanguage: (bookId, language) =>
        set((state) => {
          const updated = { ...state.bookLanguages };
          if (language) {
            updated[bookId] = language;
          } else {
            delete updated[bookId];
          }
          return { bookLanguages: updated };
        }),
      getBookLanguage: (bookId) => get().bookLanguages[bookId],
      setReaderPrefs: (prefs) =>
        set((state) => ({
          readerPrefs: { ...state.readerPrefs, ...prefs },
        })),
      updateProgress: (bookId, update) =>
        set((state) => {
          const defaults: ReadingProgress = {
            currentChapter: 0,
            scrollPercent: 0,
            lastReadAt: new Date().toISOString(),
            finished: false,
          };
          const existing = state.progress[bookId];
          return {
            progress: {
              ...state.progress,
              [bookId]: {
                ...defaults,
                ...existing,
                ...update,
                lastReadAt: new Date().toISOString(),
              },
            },
          };
        }),
      getProgress: (bookId) => get().progress[bookId] ?? null,
      mergeFromCloud: (cloudProgress, cloudLanguages, cloudPrefs) =>
        set((state) => {
          const merged = { ...state.progress };
          for (const [bookId, cloud] of Object.entries(cloudProgress)) {
            const local = merged[bookId];
            if (
              !local ||
              new Date(cloud.lastReadAt) > new Date(local.lastReadAt)
            ) {
              merged[bookId] = cloud;
            }
          }
          const mergedLangs = { ...state.bookLanguages };
          for (const [bookId, lang] of Object.entries(cloudLanguages)) {
            const localProgress = state.progress[bookId];
            const cloudP = cloudProgress[bookId];
            if (
              !localProgress ||
              (cloudP &&
                new Date(cloudP.lastReadAt) >
                  new Date(localProgress.lastReadAt))
            ) {
              mergedLangs[bookId] = lang;
            }
          }
          return {
            progress: merged,
            bookLanguages: mergedLangs,
            ...(cloudPrefs ? { readerPrefs: cloudPrefs } : {}),
          };
        }),
      markFinished: (bookId) =>
        set((state) => {
          const existing = state.progress[bookId];
          return {
            progress: {
              ...state.progress,
              [bookId]: {
                currentChapter: existing?.currentChapter ?? 1,
                scrollPercent: 100,
                lastReadAt: new Date().toISOString(),
                finished: true,
              },
            },
          };
        }),
    }),
    {
      name: "grand-old-books-reading",
    }
  )
);
