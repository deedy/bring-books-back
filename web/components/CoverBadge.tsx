"use client";

import OfflineBadge, { useIsOffline } from "@/components/OfflineBadge";

interface CoverBadgeProps {
  bookId: string;
  isNew: boolean;
  isAnthology?: boolean;
}

/**
 * Shows either the offline download badge (preferred) or the "New" badge
 * on a book cover. Offline takes priority since it's more actionable.
 */
export default function CoverBadge({ bookId, isNew, isAnthology }: CoverBadgeProps) {
  const isOffline = useIsOffline(bookId);

  if (isOffline) {
    return <OfflineBadge bookId={bookId} />;
  }

  if (isNew) {
    return (
      <span className="absolute top-3 right-3 px-2.5 py-0.5 text-[11px] font-bold rounded bg-amber-400 text-black backdrop-blur-sm uppercase tracking-wide shadow-lg shadow-amber-400/30">
        New
      </span>
    );
  }

  return null;
}
