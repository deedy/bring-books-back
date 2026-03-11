"use client";

import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import Link from "next/link";
import type { Book, Author } from "@/lib/types";
import { buildHomeBrowseModel, type HomeSortField, type HomeSortDir } from "@/lib/homeCatalog";
import { readingTime, readingTimeClock, displayYear, getNewBookIds, pageCount } from "@/lib/utils";
import CoverProgress from "@/components/CoverProgress";
import ContinueReading from "@/components/ContinueReading";
import { useReadingStore } from "@/lib/store";

interface HomeHeroProps {
  books: Book[];
  authors: Author[];
}

function LangDropdown({
  languages,
  langCounts,
  value,
  onChange,
  totalCount,
}: {
  languages: string[];
  langCounts: Record<string, number>;
  value: string;
  onChange: (v: string) => void;
  totalCount: number;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const label = value === "all" ? "All Languages" : value;

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors flex items-center gap-1 ${
          value !== "all"
            ? "bg-white/15 text-white/80"
            : "bg-white/5 text-white/40 hover:bg-white/10"
        }`}
      >
        {label}
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className={`transition-transform ${open ? "rotate-180" : ""}`}>
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {open && (
        <div className="absolute top-full mt-1 right-0 min-w-[160px] rounded-lg bg-[#1a1a1b] border border-white/10 shadow-2xl z-50 py-1">
          <button
            onClick={() => { onChange("all"); setOpen(false); }}
            className={`w-full px-3 py-1.5 text-[11px] text-left flex justify-between items-center transition-colors ${
              value === "all" ? "text-white/90 bg-white/10" : "text-white/50 hover:bg-white/5"
            }`}
          >
            <span>All Languages</span>
            <span className="text-white/30">{totalCount}</span>
          </button>
          {languages.map((l) => (
            <button
              key={l}
              onClick={() => { onChange(l); setOpen(false); }}
              className={`w-full px-3 py-1.5 text-[11px] text-left flex justify-between items-center transition-colors ${
                value === l ? "text-white/90 bg-white/10" : "text-white/50 hover:bg-white/5"
              }`}
            >
              <span>{l}</span>
              <span className="text-white/30">{langCounts[l]}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function HomeHero({ books, authors }: HomeHeroProps) {
  const [activeBookId, setActiveBookId] = useState<string | undefined>(books[0]?.id);
  const [paused, setPaused] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sort & filter state
  const [sortField, setSortField] = useState<HomeSortField>("default");
  const [sortDir, setSortDir] = useState<HomeSortDir>("asc");
  const [langFilter, setLangFilter] = useState<string>("all");

  const { languages, langCounts } = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const b of books) counts[b.originalLanguage] = (counts[b.originalLanguage] || 0) + 1;
    const sorted = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
    return { languages: sorted, langCounts: counts };
  }, [books]);

  const newBookIds = useMemo(() => getNewBookIds(books), [books]);

  const { totalWorks, totalHours } = useMemo(() => {
    let works = 0, words = 0;
    for (const b of books) {
      works += b.type === "anthology" && b.totalStories ? b.totalStories : 1;
      words += b.wordCount;
    }
    return { totalWorks: works, totalHours: Math.round(words / 230 / 60) };
  }, [books]);

  const browseModel = useMemo(() => {
    return buildHomeBrowseModel({
      books,
      langFilter,
      sortField,
      sortDir,
    });
  }, [books, sortField, sortDir, langFilter]);

  const visibleBooks = browseModel.mode === "sectioned" ? browseModel.flatBooks : browseModel.books;

  // Pick a visible featured book on first render and whenever the visible set changes.
  useEffect(() => {
    if (visibleBooks.length === 0) {
      setActiveBookId(undefined);
      return;
    }

    setActiveBookId((current) => {
      if (current && visibleBooks.some((book) => book.id === current)) return current;
      const idx = Math.floor(Math.random() * visibleBooks.length);
      return visibleBooks[idx]?.id ?? visibleBooks[0]?.id;
    });
  }, [visibleBooks]);

  const advance = useCallback(() => {
    if (visibleBooks.length === 0) return;

    setActiveBookId((prev) => {
      const idx = visibleBooks.findIndex((b) => b.id === prev);
      const next = (idx + 1) % visibleBooks.length;
      return visibleBooks[next]?.id ?? visibleBooks[0]?.id;
    });
  }, [visibleBooks]);

  useEffect(() => {
    if (paused || visibleBooks.length <= 1) return;
    timerRef.current = setInterval(advance, 5000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [paused, advance, visibleBooks.length]);

  const selectBook = useCallback((id: string) => {
    setActiveBookId(id);
    setPaused(true);
  }, []);

  // Resume carousel 8s after last manual interaction
  useEffect(() => {
    if (!paused) return;
    const t = setTimeout(() => setPaused(false), 8000);
    return () => clearTimeout(t);
  }, [paused, activeBookId]);

  const toggleSort = (field: HomeSortField) => {
    if (field === "default") {
      setSortField("default");
      setSortDir("asc");
    } else if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir(field === "length" ? "desc" : "asc");
    }
  };

  const arrow = (field: HomeSortField) => {
    if (sortField !== field) return "";
    if (field === "default") return "";
    return sortDir === "asc" ? " \u2191" : " \u2193";
  };

  const book = visibleBooks.find((b) => b.id === activeBookId) ?? visibleBooks[0];
  const author = book ? authors.find((a) => a.id === book.authorId) : undefined;
  const bookProgress = useReadingStore((s) => (book ? s.progress[book.id] : undefined));
  const isInProgress = bookProgress && bookProgress.currentChapter > 0 && !bookProgress.finished;

  if (!book || !author) return null;

  const renderBookCard = (b: Book) => {
    const bookAuthor = authors.find((a) => a.id === b.authorId);
    if (!bookAuthor) return null;

    const isActive = b.id === activeBookId;

    return (
      <Link
        key={b.id}
        href={`/books/${b.id}`}
        className="group block"
        onMouseEnter={() => selectBook(b.id)}
      >
        <div
          className={`relative aspect-[2/3] rounded-lg overflow-hidden shadow-lg transition-all duration-200 group-hover:scale-[1.03] group-hover:shadow-2xl bg-white/[0.06] ${
            isActive
              ? "ring-2 ring-offset-2 ring-offset-[#0a0a0a]"
              : ""
          }`}
          style={
            isActive
              ? ({ ringColor: b.accentColor } as React.CSSProperties)
              : undefined
          }
        >
          <img
            src={b.coverImage}
            alt={b.title}
            className="w-full h-full object-cover"
          />
          {b.type === "anthology" && b.totalStories && (
            <span className="absolute top-2 left-2 px-1.5 py-0.5 text-[10px] font-semibold rounded bg-black/60 text-white/70 backdrop-blur-sm">
              {b.totalStories} stories
            </span>
          )}
          {newBookIds.has(b.id) && (
            <span className="absolute top-2 right-2 px-1.5 py-0.5 text-[10px] font-bold rounded bg-emerald-500/90 text-white backdrop-blur-sm uppercase tracking-wide">
              New
            </span>
          )}
          <span className="absolute bottom-2 right-2 px-1.5 py-0.5 text-[10px] font-medium rounded bg-black/70 text-white/80 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
            {readingTimeClock(b.wordCount)}
          </span>
          {b.type !== "anthology" && (
            <CoverProgress bookId={b.id} totalChapters={b.totalChapters} accentColor={b.accentColor} />
          )}
          {isActive && (
            <div
              className="absolute inset-0 border-2 rounded-lg pointer-events-none"
              style={{ borderColor: b.accentColor }}
            />
          )}
        </div>
        <div className="mt-3">
          <h3 className="text-sm font-semibold text-white line-clamp-2 leading-snug">
            {b.title}
          </h3>
          <p className="text-xs text-white/50 mt-0.5">
            {bookAuthor.name}
          </p>
          <p className="text-[11px] text-white/30 mt-0.5">
            {b.type !== "anthology" && b.transliteratedTitle && b.transliteratedTitle !== b.title && (
              <><span className="italic">{b.transliteratedTitle}</span> &middot; </>
            )}
            {b.originalLanguage} &middot; {displayYear(b.originalYear, b.yearEnd)} &middot;{" "}
            {pageCount(b.wordCount)} pp &middot;{" "}
            {readingTime(b.wordCount)}
          </p>
        </div>
      </Link>
    );
  };

  return (
    <>
      {/* Hero banner — overlaps behind the fixed header */}
      <div className="relative w-full h-[350px] -mt-16">
        {/* All hero images stacked for instant crossfade */}
        {visibleBooks.map((b) => (
          <img
            key={b.id}
            src={`/data/images/heroes/${b.id}.webp`}
            alt=""
            className="absolute inset-0 w-full h-full object-cover transition-opacity duration-500"
            style={{ opacity: b.id === activeBookId ? 1 : 0 }}
          />
        ))}
        {/* Bottom fade into page bg */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,10,11,0) 0%, rgba(10,10,11,0.15) 40%, rgba(10,10,11,0.7) 70%, rgba(10,10,11,1) 100%)",
          }}
        />
      </div>

      {/* Cover + metadata — overlaps banner */}
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row gap-10 -mt-32 relative z-10">
        <div className="w-48 md:w-56 flex-shrink-0 mx-auto md:mx-0">
          <div
            className="relative aspect-[2/3] rounded-lg overflow-hidden bg-white/[0.06]"
            style={{
              boxShadow:
                "0 8px 30px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3), 0 0 60px rgba(0,0,0,0.25)",
            }}
          >
            <img
              src={book.coverImage}
              alt={book.title}
              className="w-full h-full object-cover"
            />
            {book.type === "anthology" && book.totalStories && (
              <span className="absolute top-2.5 left-2.5 px-2 py-0.5 text-[10px] font-semibold rounded bg-black/60 text-white/80 backdrop-blur-sm">
                {book.totalStories} stories
              </span>
            )}
            {newBookIds.has(book.id) && (
              <span className="absolute top-2.5 right-2.5 px-2 py-0.5 text-[10px] font-bold rounded bg-emerald-500/90 text-white backdrop-blur-sm uppercase tracking-wide">
                New
              </span>
            )}
          </div>
        </div>
        <div className="flex-1 min-w-0 drop-shadow-[0_2px_12px_rgba(0,0,0,0.6)]">
          {book.type === "anthology" && (
            <div className="flex items-center gap-1.5 mb-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/50">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
              </svg>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/50 -ml-2.5">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
              </svg>
              <span className="text-xs font-semibold uppercase tracking-widest text-white/50">Story Collection</span>
            </div>
          )}
          <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]">
            {book.title}
          </h1>
          <p className="text-lg text-white/60 mt-2">{book.subtitle}</p>
          <Link
            href={`/authors/${author.id}`}
            className="text-sm text-white/40 hover:text-white/60 transition-colors mt-1 inline-block"
          >
            by {author.name}
          </Link>

          {/* Transliterated title + native script */}
          {book.type !== "anthology" && (
            <p className="text-sm text-white/40 mt-2 italic">
              {book.title !== book.transliteratedTitle
                ? `${book.transliteratedTitle} (${book.originalTitle})`
                : book.originalTitle}
            </p>
          )}

          {/* Metadata */}
          <div className="flex flex-wrap gap-x-6 gap-y-1.5 mt-3 text-xs text-white/40">
            <span>{book.originalLanguage}</span>
            <span>{displayYear(book.originalYear, book.yearEnd)}</span>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-1.5 mt-1 text-xs text-white/40">
            <span>
              {book.type === "anthology" && book.totalStories
                ? `${book.totalStories} stories`
                : `${book.totalChapters} chapters`}
            </span>
            <span>
              {book.wordCount >= 1000
                ? `${Math.round(book.wordCount / 1000)}k`
                : book.wordCount}{" "}
              words
            </span>
            <span>{pageCount(book.wordCount)} pages</span>
            <span>{readingTime(book.wordCount)} read</span>
          </div>

          {/* Genres */}
          <div className="flex flex-wrap gap-2 mt-3">
            {book.type === "anthology" && book.totalStories && (
              <span
                className="px-2.5 py-0.5 text-[11px] font-semibold rounded-full text-white"
                style={{ backgroundColor: book.accentColor }}
              >
                {book.totalStories} stories
              </span>
            )}
            {book.genre.map((g) => (
              <span
                key={g}
                className="px-2.5 py-0.5 text-[11px] font-medium rounded-full bg-white/8 text-white/50"
              >
                {g}
              </span>
            ))}
          </div>

          <p className="text-sm text-white/45 mt-4 max-w-lg leading-relaxed line-clamp-3">
            {book.summary}
          </p>

          <Link
            href={book.type === "anthology" ? `/books/${book.id}` : isInProgress ? `/read/${book.id}/${bookProgress!.currentChapter + 1}` : `/read/${book.id}`}
            scroll={false}
            className="inline-block mt-5 px-6 py-3 rounded-lg font-medium text-white transition-opacity hover:opacity-90"
            style={{ backgroundColor: book.accentColor }}
          >
            {book.type === "anthology" ? "Explore Collection" : isInProgress ? "Continue Reading" : "Start Reading"}
          </Link>
        </div>
      </div>

      {/* Stats strip */}
      <div className="max-w-6xl mx-auto px-6 mt-12">
        <div className="flex flex-wrap justify-center gap-x-6 gap-y-1 text-[13px] text-white/40">
          <span>{totalWorks} Books</span>
          <span className="text-white/20">&middot;</span>
          <span>{languages.length} Languages</span>
          <span className="text-white/20">&middot;</span>
          <span>{totalHours}+ Hours of Reading</span>
          <span className="text-white/20">&middot;</span>
          <span>100% Free</span>
        </div>
      </div>

      {/* Feature strip */}
      <div className="flex flex-wrap justify-center gap-2 mt-8 px-6">
        {[
          { label: "Bilingual reading", image: "/data/images/features/bilingual.webp" },
          { label: "AI illustrations", image: "/data/images/features/illustrations.webp" },
          { label: "Phone-friendly", image: "/data/images/features/mobile.webp" },
          { label: "Easy explainers", image: "/data/images/features/annotations.webp" },
        ].map((feature) => (
          <div key={feature.label} className="relative group">
            <span className="px-2.5 py-1 text-[11px] font-medium rounded-full bg-white/5 text-white/40 md:hover:bg-white/10 transition-colors md:cursor-pointer inline-block">
              {feature.label}
            </span>
            {/* Desktop hover popover */}
            <div className="hidden md:block absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 opacity-0 scale-95 pointer-events-none group-hover:opacity-100 group-hover:scale-100 group-hover:pointer-events-auto transition-all duration-200 z-50">
              <div className="rounded-xl overflow-hidden shadow-2xl border border-white/10 bg-[#1a1a1b]">
                <img
                  src={feature.image}
                  alt={feature.label}
                  loading="lazy"
                  className="block max-w-[280px]"
                />
              </div>
              <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px w-3 h-3 rotate-45 bg-[#1a1a1b] border-r border-b border-white/10" />
            </div>
          </div>
        ))}
      </div>

      {/* Continue Reading */}
      <ContinueReading books={books} authors={authors} />

      {/* Our Books — hover to feature */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="flex flex-wrap items-center gap-2 mb-8">
          <h2 className="text-2xl font-bold text-white mr-auto">Our Books</h2>

          {/* Language filter */}
          <LangDropdown
            languages={languages}
            langCounts={langCounts}
            value={langFilter}
            onChange={setLangFilter}
            totalCount={books.length}
          />

          {/* Sort buttons */}
          {(["default", "year", "length"] as HomeSortField[]).map((field) => (
            <button
              key={field}
              onClick={() => toggleSort(field)}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors ${
                sortField === field
                  ? "bg-white/15 text-white/80"
                  : "bg-white/5 text-white/40 hover:bg-white/10"
              }`}
            >
              {field === "default" ? "Default" : field === "year" ? "Year" : "Length"}
              {arrow(field)}
            </button>
          ))}
        </div>

        {browseModel.mode === "sectioned" ? (
          <div className="space-y-14">
            {browseModel.sections.map((section) => (
              <div key={section.id}>
                <div className="mb-5">
                  <h3 className="text-lg font-semibold text-white">{section.title}</h3>
                  {section.description && (
                    <p className="text-sm text-white/40 mt-1">{section.description}</p>
                  )}
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
                  {section.books.map(renderBookCard)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
            {browseModel.books.map(renderBookCard)}
          </div>
        )}
      </section>
    </>
  );
}
