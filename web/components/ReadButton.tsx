"use client";

import Link from "next/link";
import { useReadingStore } from "@/lib/store";

interface ReadButtonProps {
  bookId: string;
  accentColor: string;
  totalChapters?: number;
}

export default function ReadButton({ bookId, accentColor, totalChapters }: ReadButtonProps) {
  const progress = useReadingStore((s) => s.getProgress(bookId));

  let label = "Start Reading";
  if (progress) {
    if (progress.finished) {
      label = "Read Again";
    } else if (totalChapters === 1) {
      label = "Continue Reading";
    } else {
      label = `Continue Reading (Ch. ${progress.currentChapter + 1})`;
    }
  }

  return (
    <Link
      href={`/read/${bookId}`}
      className="inline-block px-8 py-3 rounded-lg font-semibold text-white text-lg transition-opacity hover:opacity-90"
      style={{ backgroundColor: accentColor }}
    >
      {label}
    </Link>
  );
}
