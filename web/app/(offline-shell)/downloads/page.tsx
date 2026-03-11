"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { getDownloadedBooks, removeBook, subscribeOfflineBooks } from "@/lib/offline";
import { buildOfflineBookUrl, describeOfflineMode } from "@/lib/offlineUtils";
import type { OfflineBookEntry } from "@/lib/types";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

export default function DownloadsPage() {
  const [books, setBooks] = useState<OfflineBookEntry[]>([]);

  useEffect(() => {
    const refresh = () => setBooks(getDownloadedBooks());
    refresh();
    return subscribeOfflineBooks(refresh);
  }, []);

  if (!OFFLINE_ENABLED) {
    return (
      <section className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-bold text-white">Downloads</h1>
        <p className="text-white/50 mt-4">Offline reading is disabled in this environment.</p>
      </section>
    );
  }

  return (
    <section className="max-w-5xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold text-white">Downloads</h1>
      <p className="text-white/45 mt-3 max-w-2xl">
        Downloaded books live here and can be opened entirely offline.
      </p>

      {books.length === 0 ? (
        <div className="mt-10 rounded-2xl border border-white/10 bg-white/[0.03] p-8">
          <p className="text-white/60">No books saved offline yet.</p>
          <p className="text-white/35 mt-2 text-sm">
            Open any book page and use <span className="text-white/50">Save offline</span>.
          </p>
        </div>
      ) : (
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
          {books.map((book) => (
            <article
              key={book.bookId}
              className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 flex gap-4"
            >
              <img
                src={book.coverImage}
                alt={book.title}
                className="w-24 h-36 rounded-lg object-cover flex-shrink-0 bg-white/[0.06]"
              />

              <div className="min-w-0 flex-1">
                <p className="text-xs uppercase tracking-[0.18em] text-white/35">
                  {describeOfflineMode(book.mode, book.languageParam)}
                </p>
                <h2 className="text-xl font-semibold text-white mt-2 leading-tight">
                  {book.title}
                </h2>
                <p className="text-sm text-white/50 mt-1">by {book.authorName}</p>
                <p className="text-xs text-white/35 mt-3">
                  {book.totalChapters} chapters · Saved {new Date(book.cachedAt).toLocaleString()}
                </p>

                <div className="mt-5 flex flex-wrap gap-3">
                  <Link
                    href={buildOfflineBookUrl(book.bookId)}
                    className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium text-white"
                    style={{ backgroundColor: book.accentColor }}
                  >
                    Open offline
                  </Link>
                  <button
                    onClick={() => removeBook(book.bookId)}
                    className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium border border-white/10 text-white/55 hover:text-white/75 hover:bg-white/5 transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
