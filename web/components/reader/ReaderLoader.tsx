"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ChaptersData, AnnotationsData, OriginalChaptersData } from "@/lib/types";
import { SCRIPT_CONFIG } from "@/lib/scripts";
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
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(false);

    Promise.all([
      fetch(`/data/books/${bookId}/chapters.json`).then((r) => r.json()),
      fetch(`/data/books/${bookId}/meta.json`).then((r) => r.json()),
      fetch(`/data/books/${bookId}/annotations.json`)
        .then((r) => (r.ok ? r.json() : null))
        .catch(() => null),
      fetch(`/data/catalog.json`).then((r) => r.json()),
      wantsOriginal
        ? fetch(`/data/books/${bookId}/chapters_original.json`)
            .then((r) => (r.ok ? r.json() : null))
            .catch(() => null)
        : Promise.resolve(null),
    ]).then(async ([chapters, meta, annot, catalog, origData]) => {
      const book = catalog.books?.find((b: { id: string }) => b.id === bookId);
      const author = book
        ? catalog.authors?.find((a: { id: string }) => a.id === book.authorId)
        : null;
      setChaptersData(chapters);
      const resolvedMeta = {
        ...meta,
        authorName: author?.name ?? "Unknown",
        originalLanguage: book?.originalLanguage,
      };
      setBookMeta(resolvedMeta);
      if (annot) setAnnotations(annot);
      if (origData) setOriginalData(origData);

      // If showing original text, load the font and wait for it
      // before revealing the reader — prevents fallback font flicker.
      const script = resolvedMeta.originalScript as string | undefined;
      if (wantsOriginal && origData && script && script !== "Latin") {
        const scriptInfo = SCRIPT_CONFIG[script];
        if (scriptInfo) {
          const linkId = `gfont-${script}`;
          if (!document.getElementById(linkId)) {
            const familyParam = scriptInfo.googleFontFamilies.map((f) => `family=${f}`).join("&");
            const link = document.createElement("link");
            link.id = linkId;
            link.rel = "stylesheet";
            link.href = `https://fonts.googleapis.com/css2?${familyParam}&display=swap`;
            document.head.appendChild(link);
          }
          // Fast path: skip await if font is already cached
          if (!document.fonts.check(`16px "${scriptInfo.primaryFont}"`)) {
            try {
              await Promise.race([
                document.fonts.load(`16px "${scriptInfo.primaryFont}"`),
                new Promise((resolve) => setTimeout(resolve, 3000)),
              ]);
            } catch {
              // Font loading failed — proceed anyway with fallback
            }
          }
        }
      }

      setReady(true);
    });
  }, [bookId, wantsOriginal]);

  if (!ready || !chaptersData || !bookMeta) {
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
      originalScript={bookMeta.originalScript}
      initialOriginalData={originalData}
      isOriginalActive={wantsOriginal && !!originalData}
    />
  );
}
