"use client";

import { useAuth } from "@clerk/nextjs";
import { useState, useEffect, useCallback } from "react";
import {
  downloadBook,
  getDownloadedBook,
  isDownloaded,
  removeBook,
  subscribeOfflineBooks,
} from "@/lib/offline";
import { describeOfflineMode, resolveOfflineMode } from "@/lib/offlineUtils";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

interface DownloadButtonProps {
  bookId: string;
  languageParam?: string;
}

type State = "idle" | "downloading" | "downloaded" | "error";

export default function DownloadButton({ bookId, languageParam }: DownloadButtonProps) {
  const { isSignedIn } = useAuth();
  const [state, setState] = useState<State>("idle");
  const [progress, setProgress] = useState(0);
  const [supported, setSupported] = useState(true);
  const [existingLabel, setExistingLabel] = useState<string | null>(null);
  const requestedMode = resolveOfflineMode(languageParam);

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !("serviceWorker" in navigator) ||
      !("caches" in window)
    ) {
      setSupported(false);
      return;
    }

    const refresh = () => {
      const existing = getDownloadedBook(bookId);
      if (existing && !isDownloaded(bookId, languageParam)) {
        setExistingLabel(describeOfflineMode(existing.mode, existing.languageParam));
      } else {
        setExistingLabel(null);
      }

      setState(isDownloaded(bookId, languageParam) ? "downloaded" : "idle");
    };

    refresh();
    return subscribeOfflineBooks(refresh);
  }, [bookId, languageParam]);

  const handleDownload = useCallback(async () => {
    setState("downloading");
    setProgress(0);
    try {
      await downloadBook(bookId, languageParam, (pct) => setProgress(pct));
      setState("downloaded");
      setExistingLabel(null);
    } catch {
      setState("error");
    }
  }, [bookId, languageParam]);

  const handleRemove = useCallback(async () => {
    await removeBook(bookId);
    setState("idle");
    setProgress(0);
    setExistingLabel(null);
  }, [bookId]);

  if (!OFFLINE_ENABLED || !supported || !isSignedIn) return null;

  if (state === "downloading") {
    return (
      <button
        disabled
        className="inline-flex items-center gap-2.5 px-4 py-2 rounded-lg text-sm font-medium bg-white/5 text-white/50 cursor-not-allowed"
      >
        <ProgressRing percent={progress} />
        <span>Saving… {progress}%</span>
      </button>
    );
  }

  if (state === "downloaded") {
    return (
      <button
        onClick={handleRemove}
        className="group inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/5 text-white/50 hover:text-white/70 hover:bg-white/10 transition-colors"
        title="Remove offline download"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-green-400 group-hover:hidden"
        >
          <polyline points="20 6 9 17 4 12" />
        </svg>
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="hidden group-hover:block text-white/50"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
        <span className="group-hover:hidden">Saved offline</span>
        <span className="hidden group-hover:inline">Remove download</span>
      </button>
    );
  }

  if (state === "error") {
    return (
      <button
        onClick={handleDownload}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border border-yellow-500/30 text-yellow-400/80 hover:bg-yellow-500/10 transition-colors"
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        Retry download
      </button>
    );
  }

  // idle
  return (
    <button
      onClick={handleDownload}
      className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium border border-white/10 text-white/50 hover:text-white/70 hover:border-white/20 hover:bg-white/5 transition-colors"
      title={
        existingLabel
          ? `Replace saved offline copy (${existingLabel}) with ${describeOfflineMode(requestedMode, languageParam)}`
          : undefined
      }
    >
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
      >
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="7 10 12 15 17 10" />
        <line x1="12" y1="15" x2="12" y2="3" />
      </svg>
      {existingLabel ? `Replace ${existingLabel}` : "Save offline"}
    </button>
  );
}

function ProgressRing({ percent }: { percent: number }) {
  const r = 7;
  const circ = 2 * Math.PI * r;
  const offset = circ - (percent / 100) * circ;

  return (
    <svg width="20" height="20" viewBox="0 0 20 20" className="flex-shrink-0">
      <circle
        cx="10"
        cy="10"
        r={r}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        opacity="0.2"
      />
      <circle
        cx="10"
        cy="10"
        r={r}
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeDasharray={circ}
        strokeDashoffset={offset}
        strokeLinecap="round"
        transform="rotate(-90 10 10)"
        className="transition-[stroke-dashoffset] duration-200"
      />
    </svg>
  );
}
