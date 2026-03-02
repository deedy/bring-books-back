"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { Book, Author } from "@/lib/types";
import { readingTime, displayYear } from "@/lib/utils";

interface HomeHeroProps {
  books: Book[];
  authors: Author[];
}


export default function HomeHero({ books, authors }: HomeHeroProps) {
  const [activeIndex, setActiveIndex] = useState(() =>
    Math.floor(Math.random() * books.length)
  );
  const [paused, setPaused] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const advance = useCallback(() => {
    setActiveIndex((prev) => (prev + 1) % books.length);
  }, [books.length]);

  useEffect(() => {
    if (paused) return;
    timerRef.current = setInterval(advance, 5000);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [paused, advance]);

  const selectIndex = useCallback((idx: number) => {
    setActiveIndex(idx);
    setPaused(true);
  }, []);

  // Resume carousel 8s after last manual interaction
  useEffect(() => {
    if (!paused) return;
    const t = setTimeout(() => setPaused(false), 8000);
    return () => clearTimeout(t);
  }, [paused, activeIndex]);

  const book = books[activeIndex];
  const author = authors.find((a) => a.id === book.authorId)!;

  return (
    <>
      {/* Hero banner — overlaps behind the fixed header */}
      <div className="relative w-full h-[350px] -mt-16">
        {/* All hero images stacked for instant crossfade */}
        {books.map((b, idx) => (
          <img
            key={b.id}
            src={`/data/images/heroes/${b.id}.webp`}
            alt=""
            className="absolute inset-0 w-full h-full object-cover transition-opacity duration-500"
            style={{ opacity: idx === activeIndex ? 1 : 0 }}
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
            className="aspect-[2/3] rounded-lg overflow-hidden"
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
          </div>
        </div>
        <div className="flex-1 min-w-0 drop-shadow-[0_2px_12px_rgba(0,0,0,0.6)]">
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
          <p className="text-sm text-white/40 mt-2 italic">
            {book.title !== book.transliteratedTitle
              ? `${book.transliteratedTitle} (${book.originalTitle})`
              : book.originalTitle}
          </p>

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
            <span>{readingTime(book.wordCount)} read</span>
          </div>

          {/* Genres */}
          <div className="flex flex-wrap gap-2 mt-3">
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
            href={`/read/${book.id}`}
            className="inline-block mt-5 px-6 py-3 rounded-lg font-medium text-white transition-opacity hover:opacity-90"
            style={{ backgroundColor: book.accentColor }}
          >
            Start Reading
          </Link>
        </div>
      </div>

      {/* Our Books — hover to feature */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-white mb-8">Our Books</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
          {books.map((b, idx) => {
            const bookAuthor = authors.find((a) => a.id === b.authorId)!;
            const isActive = idx === activeIndex;
            return (
              <Link
                key={b.id}
                href={`/books/${b.id}`}
                className="group block"
                onMouseEnter={() => selectIndex(idx)}
              >
                <div
                  className={`relative aspect-[2/3] rounded-lg overflow-hidden shadow-lg transition-all duration-200 group-hover:scale-[1.03] group-hover:shadow-2xl ${
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
                    {b.originalLanguage} &middot; {displayYear(b.originalYear, b.yearEnd)} &middot;{" "}
                    {readingTime(b.wordCount)}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </>
  );
}
