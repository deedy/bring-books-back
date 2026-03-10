"use client";

import { useReadingStore } from "@/lib/store";

export default function CoverProgress({
  bookId,
  totalChapters,
  accentColor,
}: {
  bookId: string;
  totalChapters: number;
  accentColor: string;
}) {
  const progress = useReadingStore((s) => s.progress[bookId]);

  if (!progress || progress.finished) return null;

  const pct =
    totalChapters > 0
      ? Math.min(
          100,
          ((progress.currentChapter + progress.scrollPercent / 100) /
            totalChapters) *
            100
        )
      : 0;

  if (pct <= 0) return null;

  return (
    <div className="absolute bottom-0 left-0 right-0">
      <div className="h-1.5 bg-black/50">
        <div
          className="h-full rounded-r-full transition-all duration-300"
          style={{ width: `${pct}%`, backgroundColor: accentColor, boxShadow: `0 0 6px ${accentColor}` }}
        />
      </div>
    </div>
  );
}
