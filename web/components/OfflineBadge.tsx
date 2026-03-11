"use client";

import { useAuth } from "@clerk/nextjs";
import { useState, useEffect } from "react";
import { getDownloadedBook } from "@/lib/offline";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

export default function OfflineBadge({ bookId }: { bookId: string }) {
  const { isSignedIn } = useAuth();
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (OFFLINE_ENABLED && isSignedIn) setSaved(getDownloadedBook(bookId) !== null);
    else setSaved(false);
  }, [bookId, isSignedIn]);

  if (!saved) return null;

  return (
    <span className="absolute top-2 right-2 z-10 p-1 rounded bg-black/60 backdrop-blur-sm text-emerald-300/70">
      <svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8 2v8m0 0l-3-3m3 3l3-3M3 13h10" />
      </svg>
    </span>
  );
}

/** Returns true if the book is downloaded offline. Use to suppress other badges. */
export function useIsOffline(bookId: string): boolean {
  const { isSignedIn } = useAuth();
  const [saved, setSaved] = useState(false);
  useEffect(() => {
    if (OFFLINE_ENABLED && isSignedIn) setSaved(getDownloadedBook(bookId) !== null);
    else setSaved(false);
  }, [bookId, isSignedIn]);
  return saved;
}
