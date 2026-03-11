"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
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
  wordCount?: number;
  totalChapters?: number;
}

/** Estimate download size in MB from word count and chapter count (client-side heuristic). */
function estimateSizeMB(wordCount?: number, totalChapters?: number): number | null {
  if (!wordCount) return null;
  const chapters = totalChapters ?? 10;
  // ~6 bytes per word for text
  let bytes = wordCount * 6;
  // Chapter images ~100KB each, cover ~150KB, hero ~200KB, misc ~100KB
  bytes += chapters * 100 * 1024 + 150 * 1024 + 200 * 1024 + 100 * 1024;
  const mb = Math.max(1, Math.round(bytes / (1024 * 1024)));
  return mb;
}

type State = "idle" | "downloading" | "downloaded" | "error";

export default function DownloadButton({ bookId, languageParam, wordCount, totalChapters }: DownloadButtonProps) {
  const { isSignedIn } = useAuth();
  const [state, setState] = useState<State>("idle");
  const [progress, setProgress] = useState(0);
  const [supported, setSupported] = useState(true);
  const [existingLabel, setExistingLabel] = useState<string | null>(null);
  const requestedMode = resolveOfflineMode(languageParam);
  const sizeMB = estimateSizeMB(wordCount, totalChapters);

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
      <div className="inline-flex items-center gap-1.5">
        <Link
          href="/downloads"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/5 text-white/50 hover:text-white/70 hover:bg-white/10 transition-colors"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-green-400"
          >
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Saved offline
        </Link>
        <button
          onClick={handleRemove}
          className="p-2 rounded-lg border border-white/10 text-white/30 hover:text-red-400 hover:border-red-400/30 hover:bg-white/5 transition-colors"
          title="Remove offline download"
        >
          <TrashIcon />
        </button>
      </div>
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
      {existingLabel
        ? `Replace ${existingLabel}`
        : sizeMB
          ? `Save offline (~${sizeMB} MB)`
          : "Save offline"}
    </button>
  );
}

function TrashIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </svg>
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
