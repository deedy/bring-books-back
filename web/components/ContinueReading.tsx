"use client";

import { useMemo } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import { Book, Author } from "@/lib/types";
import { useReadingStore } from "@/lib/store";
import { readingTime } from "@/lib/utils";

interface ContinueReadingProps {
  books: Book[];
  authors: Author[];
}

export default function ContinueReading({ books, authors }: ContinueReadingProps) {
  const { isSignedIn } = useAuth();
  const progress = useReadingStore((s) => s.progress);

  const inProgressBooks = useMemo(() => {
    const entries = Object.entries(progress)
      .filter(([, p]) => p.currentChapter > 0 && !p.finished)
      .sort((a, b) => new Date(b[1].lastReadAt).getTime() - new Date(a[1].lastReadAt).getTime());

    return entries
      .map(([bookId, p]) => {
        const book = books.find((b) => b.id === bookId);
        if (!book) return null;
        const author = authors.find((a) => a.id === book.authorId);
        const pct = book.totalChapters > 0
          ? Math.min(100, ((p.currentChapter + p.scrollPercent / 100) / book.totalChapters) * 100)
          : 0;
        return { book, author, progress: p, pct };
      })
      .filter(Boolean) as Array<{
        book: Book;
        author: Author | undefined;
        progress: (typeof progress)[string];
        pct: number;
      }>;
  }, [progress, books, authors]);

  if (!isSignedIn || inProgressBooks.length === 0) return null;

  return (
    <section className="max-w-6xl mx-auto px-6 pt-10 pb-2">
      <h2 className="text-lg font-bold text-white mb-4">Continue Reading</h2>
      <div className="flex gap-4 overflow-x-auto pb-2 -mx-6 px-6 scrollbar-hide">
        {inProgressBooks.map(({ book, author, progress: p, pct }) => (
          <Link
            key={book.id}
            href={`/read/${book.id}/${p.currentChapter + 1}`}
            className="flex-shrink-0 group flex gap-3 bg-white/[0.04] hover:bg-white/[0.08] rounded-xl p-3 transition-colors"
            style={{ width: "min(320px, 80vw)" }}
          >
            <div
              className="relative w-14 h-20 flex-shrink-0 rounded-md overflow-hidden bg-white/[0.06]"
            >
              <img
                src={book.coverImage}
                alt={book.title}
                className="w-full h-full object-cover"
              />
              {/* Progress bar on cover */}
              <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/50">
                <div
                  className="h-full rounded-r-full"
                  style={{
                    width: `${pct}%`,
                    backgroundColor: book.accentColor,
                    boxShadow: `0 0 4px ${book.accentColor}`,
                  }}
                />
              </div>
            </div>
            <div className="flex-1 min-w-0 flex flex-col justify-center">
              <h3 className="text-sm font-semibold text-white line-clamp-1">
                {book.title}
              </h3>
              {author && (
                <p className="text-[11px] text-white/40 mt-0.5 line-clamp-1">
                  {author.name}
                </p>
              )}
              <div className="flex items-center gap-2 mt-1.5">
                <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${pct}%`,
                      backgroundColor: book.accentColor,
                    }}
                  />
                </div>
                <span className="text-[10px] text-white/30 whitespace-nowrap">
                  {Math.round(pct)}%
                </span>
              </div>
              <p className="text-[10px] text-white/25 mt-1">
                Ch. {p.currentChapter + 1} of {book.totalChapters} &middot; {readingTime(book.wordCount)}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
