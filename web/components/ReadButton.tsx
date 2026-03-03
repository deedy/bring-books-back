"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useReadingStore } from "@/lib/store";

interface ReadButtonProps {
  bookId: string;
  accentColor: string;
  totalChapters?: number;
  languageParam?: string;
}

export default function ReadButton({ bookId, accentColor, totalChapters, languageParam }: ReadButtonProps) {
  const progress = useReadingStore((s) => s.getProgress(bookId));
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  // Always render "Start Reading" on server; update on client after hydration
  let label = "Start Reading";
  if (mounted && progress) {
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

  if (languageParam) {
    return (
      <a href={href} className={className} style={{ backgroundColor: accentColor }}>
        {label}
      </a>
    );
  }

  return (
    <Link href={href} className={className} style={{ backgroundColor: accentColor }}>
      {label}
    </Link>
  );
}
