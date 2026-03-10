"use client";

import { useEffect, useRef } from "react";
import { useAuth } from "@clerk/nextjs";
import { useReadingStore } from "@/lib/store";
import { fetchFromCloud, syncToCloud, flushViaBeacon, mergeState } from "@/lib/sync";

export default function SyncProvider() {
  const { isSignedIn } = useAuth();
  const hasFetched = useRef(false);

  // On mount: fetch cloud data and merge
  useEffect(() => {
    if (!isSignedIn || hasFetched.current) return;
    hasFetched.current = true;

    fetchFromCloud().then((cloud) => {
      if (!cloud) return;
      const store = useReadingStore.getState();
      const local = {
        progress: store.progress,
        languages: store.bookLanguages,
      };

      const isEmpty =
        Object.keys(cloud.progress).length === 0 &&
        Object.keys(cloud.languages).length === 0;

      if (isEmpty && !cloud.readerPrefs) {
        // First-auth migration: push local data to cloud
        if (Object.keys(local.progress).length > 0) {
          syncToCloud(local.progress, local.languages, store.readerPrefs);
        }
        return;
      }

      const merged = mergeState(local, cloud);
      store.mergeFromCloud(merged.progress, merged.languages, cloud.readerPrefs);

      // If merge changed anything vs cloud, push back
      const mergedKeys = Object.keys(merged.progress);
      const cloudKeys = Object.keys(cloud.progress);
      if (
        mergedKeys.length !== cloudKeys.length ||
        mergedKeys.some(
          (k) =>
            merged.progress[k]?.lastReadAt !== cloud.progress[k]?.lastReadAt
        )
      ) {
        syncToCloud(merged.progress, merged.languages, store.readerPrefs);
      }
    });
  }, [isSignedIn]);

  // Subscribe to store changes → debounced cloud sync
  useEffect(() => {
    if (!isSignedIn) return;

    const unsub = useReadingStore.subscribe((state, prevState) => {
      if (
        state.progress !== prevState.progress ||
        state.bookLanguages !== prevState.bookLanguages ||
        state.readerPrefs !== prevState.readerPrefs
      ) {
        syncToCloud(state.progress, state.bookLanguages, state.readerPrefs);
      }
    });

    return unsub;
  }, [isSignedIn]);

  // Beacon flush on tab close
  useEffect(() => {
    if (!isSignedIn) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        const { progress, bookLanguages, readerPrefs } = useReadingStore.getState();
        flushViaBeacon(progress, bookLanguages, readerPrefs);
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [isSignedIn]);

  return null;
}
