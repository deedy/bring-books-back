"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ReadingProgress } from "./types";

interface ReadingStore {
  progress: Record<string, ReadingProgress>;
  scrollMode: "paginated" | "infinite";
  bookLanguages: Record<string, string>;
  updateProgress: (bookId: string, progress: Partial<ReadingProgress>) => void;
  getProgress: (bookId: string) => ReadingProgress | null;
  markFinished: (bookId: string) => void;
  setScrollMode: (mode: "paginated" | "infinite") => void;
  setBookLanguage: (bookId: string, language: string | undefined) => void;
  getBookLanguage: (bookId: string) => string | undefined;
}

export const useReadingStore = create<ReadingStore>()(
  persist(
    (set, get) => ({
      progress: {},
      scrollMode: "paginated" as "paginated" | "infinite",
      bookLanguages: {},
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
