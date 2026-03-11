"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import type { Chapter } from "@/lib/types";
import { useReadingStore } from "@/lib/store";
import { readingTimeExact, pageCount, chapterPath } from "@/lib/utils";

/** Hook that returns the stored language param for a book (reactive to store changes). */
function useBookLanguageParam(bookId: string): string | undefined {
  const lang = useReadingStore((s) => s.bookLanguages[bookId]);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  return mounted ? lang : undefined;
}

type ChapterSummary = Omit<Chapter, "paragraphs">;

interface ChapterListProps {
  chapters: ChapterSummary[];
  bookId: string;
  accentColor: string;
}

/** Compute the initial visible range based on reading progress. */
function initialRange(total: number, currentIdx: number | null): { start: number; end: number } | null {
  if (currentIdx === null || total <= 4) return null;
  if (currentIdx <= 1) return { start: 0, end: Math.min(4, total) };
  if (currentIdx >= total - 2) return { start: Math.max(0, total - 4), end: total };
  const start = Math.max(0, currentIdx - 1);
  const end = Math.min(total, currentIdx + 3); // exclusive
  return { start, end };
}

export default function ChapterList({ chapters, bookId, accentColor }: ChapterListProps) {
  const progress = useReadingStore((s) => s.getProgress(bookId));
  const languageParam = useBookLanguageParam(bookId);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const currentIdx = mounted && progress && !progress.finished ? progress.currentChapter : null;
  const range = initialRange(chapters.length, currentIdx);

  const [expanded, setExpanded] = useState(false);

  // Show skeleton cards until client mount so we know reading progress
  // without flickering between default and progress-based range.
  if (!mounted) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {Array.from({ length: Math.min(4, chapters.length) }, (_, i) => (
          <div key={i} className="flex flex-col gap-3 p-3 rounded-lg border border-white/[0.06] bg-white/[0.04] animate-pulse">
            <div className="w-full aspect-video rounded-t bg-white/[0.06] -mx-3 -mt-3" style={{ width: "calc(100% + 1.5rem)" }} />
            <div className="flex flex-col gap-2 py-0.5">
              <div className="flex justify-between">
                <div className="h-3 w-16 rounded bg-white/[0.06]" />
                <div className="h-3 w-24 rounded bg-white/[0.06]" />
              </div>
              <div className="h-4 w-3/4 rounded bg-white/[0.08]" />
              <div className="h-3 w-full rounded bg-white/[0.06]" />
              <div className="h-3 w-2/3 rounded bg-white/[0.06]" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  const distinctParts = new Set(chapters.map((ch) => ch.part).filter((p) => p != null));
  const hasParts = distinctParts.size > 1;

  if (hasParts) {
    const groups: { part: number; partName: string; chapters: ChapterSummary[]; globalIndices: number[] }[] = [];
    for (let gi = 0; gi < chapters.length; gi++) {
      const ch = chapters[gi];
      const last = groups[groups.length - 1];
      if (last && last.part === ch.part) {
        last.chapters.push(ch);
        last.globalIndices.push(gi);
      } else {
        groups.push({ part: ch.part ?? 0, partName: ch.partName ?? "", chapters: [ch], globalIndices: [gi] });
      }
    }

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {groups.map((group) => {
          const visibleCards: React.ReactNode[] = [];
          group.chapters.forEach((ch, i) => {
            const gi = group.globalIndices[i];
            const visible = expanded || (range ? gi >= range.start && gi < range.end : gi < 4);
            if (!visible) return;
            if (expanded && visibleCards.length === 0) {
              visibleCards.push(
                <h3
                  key={`part-${group.part}`}
                  className="col-span-1 sm:col-span-2 text-sm font-semibold text-white/40 uppercase tracking-wider mt-3 first:mt-0"
                >
                  {group.partName}
                </h3>
              );
            }
            visibleCards.push(
              <ChapterCard
                key={ch.id}
                chapter={ch}
                index={gi + 1}
                bookId={bookId}
                isCurrent={gi === currentIdx}
                accentColor={accentColor}
                languageParam={languageParam}
              />
            );
          });

          if (visibleCards.length === 0) return null;

          return visibleCards;
        })}
        {!expanded && chapters.length > (range ? range.end - range.start : 4) && (
          <button
            onClick={() => setExpanded(true)}
            className="col-span-1 sm:col-span-2 text-sm font-medium transition-colors cursor-pointer"
            style={{ color: accentColor }}
          >
            Show all {chapters.length} chapters
          </button>
        )}
      </div>
    );
  }

  // Flat list (no parts)
  const visibleChapters = expanded
    ? chapters
    : range
      ? chapters.slice(range.start, range.end)
      : chapters.slice(0, 4);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {visibleChapters.map((ch) => {
        const gi = chapters.indexOf(ch);
        return (
          <ChapterCard
            key={ch.id}
            chapter={ch}
            index={gi + 1}
            bookId={bookId}
            isCurrent={gi === currentIdx}
            accentColor={accentColor}
            languageParam={languageParam}
          />
        );
      })}
      {!expanded && chapters.length > visibleChapters.length && (
        <button
          onClick={() => setExpanded(true)}
          className="col-span-1 sm:col-span-2 text-sm font-medium transition-colors cursor-pointer"
          style={{ color: accentColor }}
        >
          Show all {chapters.length} chapters
        </button>
      )}
    </div>
  );
}

function ChapterCard({
  chapter,
  index,
  bookId,
  isCurrent,
  accentColor,
  languageParam,
}: {
  chapter: ChapterSummary;
  index: number;
  bookId: string;
  isCurrent: boolean;
  accentColor: string;
  languageParam?: string;
}) {
  const base = `/read/${bookId}/${chapterPath(chapter, index)}`;
  const href = languageParam ? `${base}?language=${languageParam}` : base;
  return (
    <Link
      href={href}
      className={`flex flex-col gap-3 p-3 rounded-lg border transition-colors group ${
        isCurrent
          ? "bg-white/[0.08] border-white/[0.15]"
          : "bg-white/[0.04] border-white/[0.06] hover:bg-white/[0.07]"
      }`}
      style={isCurrent ? { borderColor: `${accentColor}66` } : undefined}
    >
      {/* Thumbnail */}
      <div className="w-full aspect-video rounded-t overflow-hidden bg-white/[0.06] -mx-3 -mt-3" style={{ width: "calc(100% + 1.5rem)" }}>
        {chapter.image && (
          <img
            src={chapter.image}
            alt=""
            loading="lazy"
            className="w-full h-full object-cover"
          />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0 py-0.5 flex flex-col">
        <div className="flex items-center justify-between">
          <span className="text-xs text-white/40">
            Chapter {chapter.number}
            {isCurrent && (
              <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: accentColor }}>
                Reading
              </span>
            )}
          </span>
          <span className="text-xs text-white/30">{readingTimeExact(chapter.wordCount)} · {pageCount(chapter.wordCount)} pages</span>
        </div>
        <p className="text-sm font-semibold text-white mt-0.5 group-hover:text-white/90 transition-colors">
          {chapter.title}
        </p>
        {chapter.summary && (
          <p className="text-xs text-white/40 mt-1 line-clamp-3 leading-relaxed">
            {chapter.summary}
          </p>
        )}
      </div>
    </Link>
  );
}
