"use client";

import { useEffect, useState } from "react";
import { useReadingStore } from "@/lib/store";
import { ChaptersData } from "@/lib/types";
import ReadButton from "./ReadButton";

interface BookPreviewProps {
  bookId: string;
  accentColor: string;
  previewText: string;
}

export default function BookPreview({ bookId, accentColor, previewText }: BookPreviewProps) {
  const savedProgress = useReadingStore((s) => s.getProgress(bookId));
  const [text, setText] = useState(previewText);
  const [label, setLabel] = useState("Preview");

  useEffect(() => {
    if (!savedProgress) return;

    fetch(`/data/books/${bookId}/chapters.json`)
      .then((r) => r.json())
      .then((data: ChaptersData) => {
        const ch = data.chapters[savedProgress.currentChapter];
        if (!ch) return;
        const full = ch.paragraphs.join("\n\n");
        setText(full.slice(0, 800));
        const chLabel = ch.partName
          ? `${ch.partName} · Ch. ${ch.number}: ${ch.title}`
          : `Ch. ${ch.number}: ${ch.title}`;
        setLabel(`Continue Reading · ${chLabel}`);
      })
      .catch(() => {});
  }, [bookId, savedProgress]);

  return (
    <section className="mt-16">
      <h2 className="text-xl font-bold text-white mb-4">{label}</h2>
      <div className="relative max-w-3xl">
        <p
          className="text-white/50 leading-relaxed"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {text}
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0a0a0a] to-transparent" />
      </div>
      <div className="mt-6">
        <ReadButton bookId={bookId} accentColor={accentColor} />
      </div>
    </section>
  );
}
