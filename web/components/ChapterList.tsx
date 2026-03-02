"use client";

import { useState } from "react";
import Link from "next/link";
import type { Chapter } from "@/lib/types";
import { useReadingStore } from "@/lib/store";
import { readingTime, chapterPath } from "@/lib/utils";

type ChapterSummary = Omit<Chapter, "paragraphs">;

interface ChapterListProps {
  chapters: ChapterSummary[];
  bookId: string;
  accentColor: string;
}

/** Compute the initial visible range based on reading progress. */
function initialRange(total: number, currentIdx: number | null): { start: number; end: number } | null {
  if (currentIdx === null || total <= 3) return null;
  const start = Math.max(0, currentIdx - 1);
  const end = Math.min(total, currentIdx + 2); // exclusive
  return { start, end };
}

export default function ChapterList({ chapters, bookId, accentColor }: ChapterListProps) {
  const progress = useReadingStore((s) => s.getProgress(bookId));
  const currentIdx = progress && !progress.finished ? progress.currentChapter : null;
  const range = initialRange(chapters.length, currentIdx);

  const [expanded, setExpanded] = useState(false);

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
      <div className="space-y-6">
        {groups.map((group) => {
          const groupCards = group.chapters.map((ch, i) => {
            const gi = group.globalIndices[i];
            const visible = expanded || (range ? gi >= range.start && gi < range.end : gi < 3);
            if (!visible) return null;
            return (
              <ChapterCard
                key={ch.id}
                chapter={ch}
                index={gi + 1}
                bookId={bookId}
                isCurrent={gi === currentIdx}
                accentColor={accentColor}
              />
            );
          });

          if (!expanded && groupCards.every((c) => c === null)) return null;

          return (
            <div key={group.part}>
              <h3 className="text-sm font-semibold text-white/40 uppercase tracking-wider mb-3">
                Part {group.part} — {group.partName}
              </h3>
              <div className="space-y-2">{groupCards}</div>
            </div>
          );
        })}
        {!expanded && chapters.length > (range ? range.end - range.start : 3) && (
          <button
            onClick={() => setExpanded(true)}
            className="text-sm font-medium transition-colors cursor-pointer"
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
      : chapters.slice(0, 3);

  return (
    <div className="space-y-2">
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
          />
        );
      })}
      {!expanded && chapters.length > visibleChapters.length && (
        <button
          onClick={() => setExpanded(true)}
          className="text-sm font-medium transition-colors mt-4 cursor-pointer"
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
}: {
  chapter: ChapterSummary;
  index: number;
  bookId: string;
  isCurrent: boolean;
  accentColor: string;
}) {
  const href = `/read/${bookId}/${chapterPath(chapter, index)}`;
  const time = readingTime(chapter.wordCount);

  return (
    <Link
      href={href}
      className={`flex flex-col sm:flex-row gap-3 sm:gap-4 items-start p-3 rounded-lg border transition-colors group ${
        isCurrent
          ? "bg-white/[0.08] border-white/[0.15]"
          : "bg-white/[0.04] border-white/[0.06] hover:bg-white/[0.07]"
      }`}
      style={isCurrent ? { borderColor: `${accentColor}66` } : undefined}
    >
      {/* Thumbnail */}
      <div className="w-full sm:w-[120px] flex-shrink-0 aspect-video rounded overflow-hidden bg-white/[0.06]">
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
      <div className="flex-1 min-w-0 py-0.5">
        <div className="flex items-center justify-between gap-2">
          <span className="text-xs text-white/40">
            Chapter {chapter.number}
            {isCurrent && (
              <span className="ml-2 text-[10px] font-semibold uppercase tracking-wider" style={{ color: accentColor }}>
                Reading
              </span>
            )}
          </span>
          <span className="text-xs text-white/30 flex-shrink-0">{time}</span>
        </div>
        <p className="text-sm font-semibold text-white mt-0.5 group-hover:text-white/90 transition-colors">
          {chapter.title}
        </p>
        {chapter.summary && (
          <p className="text-xs text-white/40 mt-1 sm:line-clamp-2 leading-relaxed">
            {chapter.summary}
          </p>
        )}
      </div>
    </Link>
  );
}
