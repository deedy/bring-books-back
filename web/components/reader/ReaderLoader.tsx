"use client";

import { useEffect, useState } from "react";
import { ChaptersData, AnnotationsData } from "@/lib/types";
import ReaderView from "./ReaderView";

interface ReaderLoaderProps {
  bookId: string;
  initialChapter?: number;
}

export default function ReaderLoader({ bookId, initialChapter }: ReaderLoaderProps) {
  const [chaptersData, setChaptersData] = useState<ChaptersData | null>(null);
  const [bookMeta, setBookMeta] = useState<{
    title: string;
    accentColor: string;
    totalChapters: number;
    authorName: string;
    coverImage: string;
    originalYear: number;
  } | null>(null);
  const [annotations, setAnnotations] = useState<AnnotationsData | undefined>(undefined);

  useEffect(() => {
    Promise.all([
      fetch(`/data/books/${bookId}/chapters.json`).then((r) => r.json()),
      fetch(`/data/books/${bookId}/meta.json`).then((r) => r.json()),
      fetch(`/data/books/${bookId}/annotations.json`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`/data/catalog.json`).then((r) => r.json()),
    ]).then(([chapters, meta, annot, catalog]) => {
      const book = catalog.books?.find((b: { id: string }) => b.id === bookId);
      const author = book
        ? catalog.authors?.find((a: { id: string }) => a.id === book.authorId)
        : null;
      setChaptersData(chapters);
      setBookMeta({ ...meta, authorName: author?.name ?? "Unknown" });
      if (annot) setAnnotations(annot);
    });
  }, [bookId]);

  if (!chaptersData || !bookMeta) {
    return (
      <div className="fixed inset-0 bg-[#1a1a1a] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <ReaderView
      bookId={bookId}
      bookTitle={bookMeta.title}
      authorName={bookMeta.authorName}
      accentColor={bookMeta.accentColor}
      coverImage={bookMeta.coverImage}
      originalYear={bookMeta.originalYear}
      chapters={chaptersData.chapters}
      totalChapters={bookMeta.totalChapters}
      initialChapter={initialChapter}
      annotations={annotations}
    />
  );
}
