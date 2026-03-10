"use client";

import { ReadingProgress } from "@/lib/types";

interface ReadButtonProps {
  bookId: string;
  accentColor: string;
  totalChapters?: number;
  languageParam?: string;
  progress?: ReadingProgress | null;
}

export default function ReadButton({ bookId, accentColor, totalChapters, languageParam, progress }: ReadButtonProps) {
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

  const langSuffix = languageParam ? `?language=${languageParam}` : "";
  const href = `/read/${bookId}${langSuffix}`;
  const className = "inline-block px-8 py-3 rounded-lg font-semibold text-white text-lg transition-opacity hover:opacity-90";

  // Always use <a> (full page load) instead of Next.js Link to ensure
  // ReaderView fully remounts and restores scroll position from Zustand.
  return (
    <a href={href} className={className} style={{ backgroundColor: accentColor }}>
      {label}
    </a>
  );
}
