"use client";

import { useEffect, useState, useRef } from "react";
import { useSearchParams } from "next/navigation";
import { ChaptersData, AnnotationsData, OriginalChaptersData } from "@/lib/types";
import ReaderView from "./ReaderView";

interface ReaderLoaderProps {
  bookId: string;
  initialChapter?: number;
}

export default function ReaderLoader({ bookId, initialChapter }: ReaderLoaderProps) {
  const searchParams = useSearchParams();
  const language = searchParams.get("language");
  const wantsOriginal = !!language && language.toLowerCase() !== "english";

  const [chaptersData, setChaptersData] = useState<ChaptersData | null>(null);
  const [originalData, setOriginalData] = useState<OriginalChaptersData | null>(null);
  const [bookMeta, setBookMeta] = useState<{
    title: string;
    accentColor: string;
    totalChapters: number;
    authorName: string;
    coverImage: string;
    originalYear: number;
    hasOriginalText?: boolean;
    originalLanguage?: string;
    originalScript?: string;
  } | null>(null);
  const [annotations, setAnnotations] = useState<AnnotationsData | undefined>(undefined);

  // Load base data (English chapters, meta, annotations, catalog)
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
      setBookMeta({
        ...meta,
        authorName: author?.name ?? "Unknown",
        originalLanguage: book?.originalLanguage,
      });
      if (annot) setAnnotations(annot);
    });
  }, [bookId]);

  // Load original chapters when language param requests it and book supports it
  const fetchedOriginalRef = useRef(false);
  useEffect(() => {
    if (
      wantsOriginal &&
      bookMeta?.hasOriginalText &&
      !originalData &&
      !fetchedOriginalRef.current
    ) {
      fetchedOriginalRef.current = true;
      fetch(`/data/books/${bookId}/chapters_original.json`)
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (data) setOriginalData(data);
        })
        .catch(() => {});
    }
  }, [bookId, wantsOriginal, bookMeta?.hasOriginalText, originalData]);

  // Not ready until base data loaded AND original fetched if needed
  const needsOriginal = wantsOriginal && bookMeta?.hasOriginalText;
  const ready = chaptersData && bookMeta && (!needsOriginal || originalData);

  if (!ready) {
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
      hasOriginalText={bookMeta.hasOriginalText}
      originalLanguage={bookMeta.originalLanguage}
      originalScript={bookMeta.originalScript}
      initialOriginalData={originalData}
      isOriginalActive={wantsOriginal && !!originalData}
    />
  );
}
