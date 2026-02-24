"use client";

import { useState } from "react";
import Link from "next/link";
import { Book, Author } from "@/lib/types";

interface HomeHeroProps {
  books: Book[];
  authors: Author[];
}

export default function HomeHero({ books, authors }: HomeHeroProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const book = books[activeIndex];
  const author = authors.find((a) => a.id === book.authorId)!;

  return (
    <>
      {/* Hero — updates on hover */}
      <section className="relative py-20 px-6 overflow-hidden">
        <div
          className="absolute inset-0 opacity-20 transition-all duration-500"
          style={{
            background: `radial-gradient(ellipse at 30% 50%, ${book.accentColor}, transparent 70%)`,
          }}
        />
        <div className="relative max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-12">
          <div className="w-48 md:w-56 flex-shrink-0">
            <div className="aspect-[2/3] rounded-lg overflow-hidden shadow-2xl transition-all duration-300">
              <img
                src={book.coverImage}
                alt={book.title}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
          <div className="text-center md:text-left flex-1 min-w-0">
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
              {book.title}
            </h1>
            <p className="text-lg text-white/60 mt-2">{book.subtitle}</p>
            <Link
              href={`/authors/${author.id}`}
              className="text-sm text-white/40 hover:text-white/60 transition-colors mt-1 inline-block"
            >
              by {author.name}
            </Link>

            {/* Metadata grid */}
            <div className="flex flex-wrap gap-x-6 gap-y-1.5 mt-4 text-xs text-white/40">
              <span>{book.originalLanguage}</span>
              <span>{book.originalYear}</span>
              <span className="italic">{book.originalTitle}</span>
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-1.5 mt-1 text-xs text-white/40">
              <span>{book.totalChapters} chapters</span>
              <span>
                {book.wordCount >= 1000
                  ? `${Math.round(book.wordCount / 1000)}k`
                  : book.wordCount}{" "}
                words
              </span>
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
      </section>

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
                onMouseEnter={() => setActiveIndex(idx)}
              >
                <div
                  className={`relative aspect-[2/3] rounded-lg overflow-hidden shadow-lg transition-all duration-200 group-hover:scale-[1.03] group-hover:shadow-2xl ${
                    isActive ? "ring-2 ring-offset-2 ring-offset-[#0a0a0a]" : ""
                  }`}
                  style={isActive ? { ringColor: b.accentColor } as React.CSSProperties : undefined}
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
                  <h3 className="text-sm font-semibold text-white truncate">
                    {b.title}
                  </h3>
                  <p className="text-xs text-white/50 mt-0.5">
                    {bookAuthor.name}
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
