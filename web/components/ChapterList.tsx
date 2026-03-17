"use client";

import { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import type { Chapter, SectionInfo } from "@/lib/types";
import { useReadingStore } from "@/lib/store";
import { readingTimeExact, formatAudioDuration, pageCount, chapterPath, sectionTitle, sectionsHaveTitles } from "@/lib/utils";
import HeadphoneIcon from "@/components/icons/HeadphoneIcon";

type ChapterSortField = "default" | "length";
type ChapterSortDir = "asc" | "desc";

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
  heading?: string;
  buildHref?: (targetPath: string, languageParam?: string, hash?: string) => string;
  audioDurations?: Record<string, number>;
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

function defaultChapterHrefBuilder(bookId: string, targetPath: string, languageParam?: string, hash?: string) {
  const base = `/read/${bookId}/${targetPath}`;
  const query = languageParam ? `?language=${encodeURIComponent(languageParam)}` : "";
  return `${base}${query}${hash ?? ""}`;
}

export default function ChapterList({
  chapters,
  bookId,
  accentColor,
  heading,
  buildHref,
  audioDurations,
}: ChapterListProps) {
  const progress = useReadingStore((s) => s.getProgress(bookId));
  const languageParam = useBookLanguageParam(bookId);
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const currentIdx = mounted && progress && !progress.finished ? progress.currentChapter : null;

  const [expanded, setExpanded] = useState(false);
  const [sortField, setSortField] = useState<ChapterSortField>("default");
  const [sortDir, setSortDir] = useState<ChapterSortDir>("asc");

  // Build sorted chapters with original indices preserved
  const sortedChapters = useMemo(() => {
    const indexed = chapters.map((ch, i) => ({ ch, originalIndex: i }));
    if (sortField === "length") {
      indexed.sort((a, b) =>
        sortDir === "asc"
          ? a.ch.wordCount - b.ch.wordCount
          : b.ch.wordCount - a.ch.wordCount
      );
    } else if (sortField === "default" && sortDir === "desc") {
      indexed.reverse();
    }
    return indexed;
  }, [chapters, sortField, sortDir]);

  const toggleSort = (field: ChapterSortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir(field === "length" ? "desc" : "asc");
      if (!expanded) setExpanded(true);
    }
  };

  const arrow = (field: ChapterSortField) => {
    if (sortField !== field) return "";
    return sortDir === "asc" ? " \u2191" : " \u2193";
  };

  const isSorted = sortField !== "default" || sortDir === "desc";
  const range = isSorted ? null : initialRange(chapters.length, currentIdx);

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
      <div>
        <div className="flex items-center justify-between mb-6">
          {heading && <h2 className="text-xl font-bold text-white">{heading}</h2>}
          {chapters.length > 4 && (
            <div className="flex items-center gap-1.5">
              {(["default", "length"] as ChapterSortField[]).map((field) => (
                <button
                  key={field}
                  onClick={() => toggleSort(field)}
                  className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors ${
                    sortField === field
                      ? "bg-white/15 text-white/80"
                      : "bg-white/5 text-white/40 hover:bg-white/10"
                  }`}
                >
                  {field === "default" ? "Order" : "Length"}
                  {arrow(field)}
                </button>
              ))}
            </div>
          )}
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {isSorted ? (
          // Sorted: flat list, no part grouping
          <>
            {(expanded ? sortedChapters : sortedChapters.slice(0, 4)).map(({ ch, originalIndex }) => (
              <ChapterCard
                key={ch.id}
                chapter={ch}
                index={originalIndex + 1}
                bookId={bookId}
                isCurrent={originalIndex === currentIdx}
                accentColor={accentColor}
                languageParam={languageParam}
                buildHref={buildHref}
                audioDurationSec={audioDurations?.[ch.id]}
              />
            ))}
          </>
        ) : (
          // Default order: grouped by parts
          groups.map((group) => {
            const visibleCards: React.ReactNode[] = [];
            group.chapters.forEach((ch, i) => {
              const gi = group.globalIndices[i];
              const visible = expanded || (range ? gi >= range.start && gi < range.end : gi < 4);
              if (!visible) return;
              if (visibleCards.length === 0) {
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
                  buildHref={buildHref}
                  audioDurationSec={audioDurations?.[ch.id]}
                />
              );
            });

            if (visibleCards.length === 0) return null;
            return visibleCards;
          })
        )}
        {!expanded && chapters.length > (isSorted ? 4 : (range ? range.end - range.start : 4)) && (
          <button
            onClick={() => setExpanded(true)}
            className="col-span-1 sm:col-span-2 text-sm font-medium transition-colors cursor-pointer"
            style={{ color: accentColor }}
          >
            Show all {chapters.length} chapters
          </button>
        )}
        </div>
      </div>
    );
  }

  // Flat list (no parts)
  const visibleItems = expanded
    ? sortedChapters
    : range
      ? sortedChapters.filter(({ originalIndex }) => originalIndex >= range.start && originalIndex < range.end)
      : sortedChapters.slice(0, 4);

  const headerRow = (
    <div className="flex items-center justify-between mb-6">
      {heading && <h2 className="text-xl font-bold text-white">{heading}</h2>}
      {chapters.length > 4 && (
        <div className="flex items-center gap-1.5">
          {(["default", "length"] as ChapterSortField[]).map((field) => (
            <button
              key={field}
              onClick={() => toggleSort(field)}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors ${
                sortField === field
                  ? "bg-white/15 text-white/80"
                  : "bg-white/5 text-white/40 hover:bg-white/10"
              }`}
            >
              {field === "default" ? "Order" : "Length"}
              {arrow(field)}
            </button>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div>
      {headerRow}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {visibleItems.map(({ ch, originalIndex }) => (
          <ChapterCard
            key={ch.id}
            chapter={ch}
            index={originalIndex + 1}
            bookId={bookId}
            isCurrent={originalIndex === currentIdx}
            accentColor={accentColor}
            languageParam={languageParam}
            buildHref={buildHref}
            audioDurationSec={audioDurations?.[ch.id]}
          />
        ))}
        {!expanded && chapters.length > visibleItems.length && (
          <button
            onClick={() => setExpanded(true)}
            className="col-span-1 sm:col-span-2 text-sm font-medium transition-colors cursor-pointer"
            style={{ color: accentColor }}
          >
            Show all {chapters.length} chapters
          </button>
        )}
      </div>
    </div>
  );
}

function SectionGridBookView({
  sections,
  bookId,
  chapterIndex,
  accentColor,
  languageParam,
  buildHref,
}: {
  sections: SectionInfo[];
  bookId: string;
  chapterIndex: number;
  accentColor: string;
  languageParam?: string;
  buildHref?: (targetPath: string, languageParam?: string, hash?: string) => string;
}) {
  const [filter, setFilter] = useState("");

  const sectionHref = (sec: SectionInfo) => {
    const targetPath = chapterIndex.toString();
    return (buildHref ?? ((path, lang, hash) => defaultChapterHrefBuilder(bookId, path, lang, hash)))(
      targetPath,
      languageParam,
      `#section-${sec.number}`,
    );
  };

  const hasTitles = sectionsHaveTitles(sections);

  const filteredSections = filter
    ? sections.filter((sec) => {
        const q = filter.toLowerCase();
        if (String(sec.number).startsWith(q)) return true;
        const title = sectionTitle(sec.label);
        if (title && title.toLowerCase().includes(q)) return true;
        return sec.label.toLowerCase().includes(q);
      })
    : sections;

  return (
    <div className="mt-2 pt-2 border-t border-white/[0.06]">
      {sections.length >= 10 && (
        <div className="mb-2">
          <input
            type="text"
            placeholder={hasTitles ? "Filter sections…" : `Filter sections (1–${sections[sections.length - 1]?.number ?? ""})`}
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            onClick={(e) => e.preventDefault()}
            className="w-full text-xs bg-white/5 border border-white/10 rounded px-2 py-1.5 text-white/70 placeholder-white/20 outline-none focus:border-white/20"
          />
        </div>
      )}
      {hasTitles ? (
        <div className="flex flex-col gap-0.5 max-h-[200px] overflow-y-auto scrollbar-thin">
          {filteredSections.map((sec) => {
            const title = sectionTitle(sec.label);
            return (
              <a
                key={sec.paragraphIndex}
                href={sectionHref(sec)}
                onClick={(e) => e.stopPropagation()}
                className="text-left px-1.5 py-1 rounded transition-colors flex items-baseline gap-2 text-white/40 hover:text-white/70 hover:bg-white/10"
                title={sec.label}
              >
                <span className="text-[10px] tabular-nums w-5 text-right flex-shrink-0 opacity-60">{sec.number}</span>
                <span className="text-[12px] line-clamp-1">{title ?? sec.label}</span>
              </a>
            );
          })}
        </div>
      ) : (
        <div className="grid grid-cols-8 gap-1 max-h-[160px] overflow-y-auto scrollbar-thin">
          {filteredSections.map((sec) => (
            <a
              key={sec.paragraphIndex}
              href={sectionHref(sec)}
              onClick={(e) => e.stopPropagation()}
              className="text-[11px] py-1 rounded text-center transition-colors tabular-nums text-white/40 hover:text-white/70 hover:bg-white/10"
              title={sec.label}
            >
              {sec.number}
            </a>
          ))}
        </div>
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
  buildHref,
  audioDurationSec,
}: {
  chapter: ChapterSummary;
  index: number;
  bookId: string;
  isCurrent: boolean;
  accentColor: string;
  languageParam?: string;
  buildHref?: (targetPath: string, languageParam?: string, hash?: string) => string;
  audioDurationSec?: number;
}) {
  const [sectionsExpanded, setSectionsExpanded] = useState(false);
  const hasSections = !!chapter.sections && chapter.sections.length > 0;

  const hrefBuilder = buildHref ?? ((targetPath, lang, hash) => defaultChapterHrefBuilder(bookId, targetPath, lang, hash));
  const href = hrefBuilder(chapterPath(chapter, index), languageParam);
  return (
    <div
      className={`flex flex-col gap-3 p-3 rounded-lg border transition-colors group ${
        isCurrent
          ? "bg-white/[0.08] border-white/[0.15]"
          : "bg-white/[0.04] border-white/[0.06] hover:bg-white/[0.07]"
      }`}
      style={isCurrent ? { borderColor: `${accentColor}66` } : undefined}
    >
      <Link href={href} className="flex-1 flex flex-col gap-3">
        {/* Thumbnail */}
        <div className="relative w-full aspect-video rounded-t overflow-hidden bg-white/[0.06] -mx-3 -mt-3" style={{ width: "calc(100% + 1.5rem)" }}>
          {chapter.image && (
            <img
              src={chapter.image}
              alt=""
              loading="lazy"
              className="w-full h-full object-cover"
            />
          )}
          {audioDurationSec && (
            <div
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                window.location.href = `${href}${href.includes("?") ? "&" : "?"}autoplay=1`;
              }}
              className="absolute inset-0 flex items-center justify-center bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                <polygon points="6,3 20,12 6,21" />
              </svg>
            </div>
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
            <span className="text-xs text-white/30">
              {audioDurationSec ? (
                <>
                  <HeadphoneIcon size={12} className="inline -mt-px mr-1.5" />
                  {formatAudioDuration(audioDurationSec)} · {pageCount(chapter.wordCount)} pages
                </>
              ) : (
                <>{readingTimeExact(chapter.wordCount)} · {pageCount(chapter.wordCount)} pages</>
              )}
            </span>
          </div>
          <p className="text-sm font-semibold text-white mt-0.5 group-hover:text-white/90 transition-colors">
            {chapter.title}
            {chapter.subtitle && (
              <span className="text-xs text-white/35 font-normal ml-2">{chapter.subtitle}</span>
            )}
          </p>
          {chapter.summary && (
            <p className="text-xs text-white/40 mt-1 line-clamp-3 leading-relaxed">
              {chapter.summary}
            </p>
          )}
        </div>
      </Link>

      {/* Section toggle + grid */}
      {hasSections && (
        <>
          <button
            onClick={() => setSectionsExpanded(!sectionsExpanded)}
            className="flex items-center gap-1.5 text-[11px] text-white/30 hover:text-white/60 transition-colors self-start mt-auto"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className={`transition-transform ${sectionsExpanded ? "rotate-90" : ""}`}
            >
              <polyline points="9 18 15 12 9 6" />
            </svg>
            {sectionsExpanded ? `Hide ${chapter.sections!.length} sections` : `${chapter.sections!.length} sections`}
          </button>
          {sectionsExpanded && (
            <SectionGridBookView
              sections={chapter.sections!}
              bookId={bookId}
              chapterIndex={index}
              accentColor={accentColor}
              languageParam={languageParam}
              buildHref={buildHref}
            />
          )}
        </>
      )}
    </div>
  );
}
