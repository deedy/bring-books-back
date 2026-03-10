"use client";

import { useMemo } from "react";
import { useReadingStore } from "@/lib/store";
import ReadButton from "./ReadButton";

interface BookPreviewProps {
  bookId: string;
  accentColor: string;
  previewText: string;
}

export default function BookPreview({ bookId, accentColor, previewText }: BookPreviewProps) {
  const savedProgress = useReadingStore((s) => s.getProgress(bookId));
  const label = useMemo(() => {
    if (!savedProgress) return "Preview";
    return savedProgress.finished ? "Read Again" : "Continue Reading";
  }, [savedProgress]);

  return (
    <section className="mt-16">
      <h2 className="text-xl font-bold text-white mb-4">{label}</h2>
      <div className="relative max-w-3xl">
        <p
          className="text-white/50 leading-relaxed"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {previewText}
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0a0a0a] to-transparent" />
      </div>
      <div className="mt-6">
        <ReadButton bookId={bookId} accentColor={accentColor} progress={savedProgress} />
      </div>
    </section>
  );
}
