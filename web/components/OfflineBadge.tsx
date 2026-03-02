"use client";

import { useState, useEffect } from "react";
import { isDownloaded } from "@/lib/offline";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

export default function OfflineBadge({ bookId }: { bookId: string }) {
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (OFFLINE_ENABLED) setSaved(isDownloaded(bookId));
  }, [bookId]);

  if (!saved) return null;

  return (
    <span className="absolute top-2 right-2 z-10 flex items-center gap-1 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[10px] text-green-400 font-medium">
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
        <polyline points="20 6 9 17 4 12" />
      </svg>
      Offline
    </span>
  );
}
