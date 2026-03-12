"use client";

import { useAuth } from "@clerk/nextjs";
import Link from "next/link";
import { redirect } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { getDownloadedBooks, removeBook, subscribeOfflineBooks } from "@/lib/offline";
import { buildOfflineBookUrl, describeOfflineMode } from "@/lib/offlineUtils";
import { useReadingStore } from "@/lib/store";
import type { OfflineBookEntry } from "@/lib/types";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

function timeAgo(dateString: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(dateString).toLocaleDateString();
}

function TrashIcon({ size = 13 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6" />
      <path d="M14 11v6" />
    </svg>
  );
}

function ConfirmDeleteModal({
  book,
  onConfirm,
  onCancel,
}: {
  book: OfflineBookEntry;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCancel();
    };
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [onCancel]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onCancel} />
      <div className="relative bg-[#1a1a1a] border border-white/10 rounded-xl p-6 max-w-sm w-full shadow-2xl">
        <h3 className="text-base font-semibold text-white">Remove download?</h3>
        <p className="text-sm text-white/45 mt-2 leading-relaxed">
          <span className="text-white/70">{book.title}</span> will be removed from this device.
          You can re-download it anytime.
        </p>
        <div className="flex gap-3 mt-5">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-lg text-sm font-medium border border-white/10 text-white/60 hover:text-white/80 hover:bg-white/5 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 rounded-lg text-sm font-medium bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30 transition-colors"
          >
            Remove
          </button>
        </div>
      </div>
    </div>
  );
}

function DownloadCard({
  book,
  onRequestDelete,
}: {
  book: OfflineBookEntry;
  onRequestDelete: (book: OfflineBookEntry) => void;
}) {
  const progress = useReadingStore((s) => s.getProgress(book.bookId));
  const pct =
    progress && book.totalChapters > 0
      ? Math.min(100, ((progress.currentChapter + progress.scrollPercent / 100) / book.totalChapters) * 100)
      : 0;
  const hasProgress = progress && progress.currentChapter > 0 && !progress.finished;

  return (
    <article className="group relative rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-colors overflow-hidden">
      {/* Accent bar */}
      <div className="h-0.5" style={{ backgroundColor: book.accentColor, opacity: 0.5 }} />

      <div className="p-4 flex gap-4">
        {/* Cover with progress overlay */}
        <Link
          href={buildOfflineBookUrl(book.bookId)}
          className="relative w-20 h-[120px] flex-shrink-0 rounded-lg overflow-hidden bg-white/[0.06] shadow-lg"
        >
          <img
            src={book.coverImage}
            alt={book.title}
            className="w-full h-full object-cover"
          />
          {hasProgress && (
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/60">
              <div
                className="h-full rounded-r-full"
                style={{
                  width: `${pct}%`,
                  backgroundColor: book.accentColor,
                  boxShadow: `0 0 4px ${book.accentColor}`,
                }}
              />
            </div>
          )}
        </Link>

        {/* Details */}
        <div className="min-w-0 flex-1 flex flex-col">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <Link
                href={buildOfflineBookUrl(book.bookId)}
                className="text-base font-semibold text-white leading-tight line-clamp-2 hover:text-white/80 transition-colors"
                style={{ fontFamily: "var(--font-serif)" }}
              >
                {book.title}
              </Link>
              <p className="text-xs text-white/40 mt-0.5">{book.authorName}</p>
            </div>
            <button
              onClick={() => onRequestDelete(book)}
              className="p-1.5 rounded-md border border-white/[0.06] text-white/20 hover:text-red-400 hover:border-red-400/20 hover:bg-red-400/5 transition-colors flex-shrink-0"
              title="Remove download"
            >
              <TrashIcon />
            </button>
          </div>

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5 mt-2 text-[11px] text-white/30">
            {book.mode !== "english" && (
              <span className="px-1.5 py-0.5 rounded bg-white/[0.06] text-white/40 text-[10px] font-medium">
                {describeOfflineMode(book.mode, book.languageParam)}
              </span>
            )}
            <span>{book.totalChapters === 1 ? "Short story" : `${book.totalChapters} ch`}</span>
            {book.estimatedSizeMB && <span>~{book.estimatedSizeMB} MB</span>}
            <span>Saved {timeAgo(book.cachedAt)}</span>
          </div>

          {/* Progress bar */}
          {hasProgress && (
            <div className="flex items-center gap-2 mt-3">
              <div className="flex-1 h-1 bg-white/[0.08] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${pct}%`, backgroundColor: book.accentColor }}
                />
              </div>
              <span className="text-[10px] text-white/25 tabular-nums whitespace-nowrap">
                {Math.round(pct)}%
              </span>
            </div>
          )}

          {/* Actions */}
          <div className="mt-auto pt-3">
            <Link
              href={buildOfflineBookUrl(book.bookId)}
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-medium text-white transition-opacity hover:opacity-85"
              style={{ backgroundColor: book.accentColor }}
            >
              {hasProgress
                ? `Continue · Ch. ${progress.currentChapter + 1}`
                : progress?.finished
                  ? "Read again"
                  : "Start reading"}
            </Link>
          </div>
        </div>
      </div>
    </article>
  );
}

export default function DownloadsPage() {
  const { isLoaded, isSignedIn } = useAuth();
  const [books, setBooks] = useState<OfflineBookEntry[]>([]);
  const [pendingDelete, setPendingDelete] = useState<OfflineBookEntry | null>(null);

  useEffect(() => {
    const refresh = () => setBooks(getDownloadedBooks());
    refresh();
    return subscribeOfflineBooks(refresh);
  }, []);

  if (isLoaded && !isSignedIn) {
    redirect("/sign-in?redirect_url=%2Fdownloads");
  }

  const handleConfirmDelete = useCallback(async () => {
    if (!pendingDelete) return;
    await removeBook(pendingDelete.bookId);
    setPendingDelete(null);
  }, [pendingDelete]);

  const handleCancelDelete = useCallback(() => {
    setPendingDelete(null);
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
    <section className="max-w-4xl mx-auto px-6 py-16">
      <div className="flex items-end justify-between mb-8">
        <div>
          <h1
            className="text-2xl font-bold text-white"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            Downloads
          </h1>
          <p className="text-sm text-white/35 mt-1">
            {books.length === 0
              ? "Save books for offline reading"
              : `${books.length} book${books.length === 1 ? "" : "s"} saved for offline reading`}
          </p>
        </div>
        {books.length > 0 && (
          <Link
            href="/"
            className="text-xs text-white/30 hover:text-white/60 transition-colors"
          >
            Browse more
          </Link>
        )}
      </div>

      {books.length === 0 ? (
        <div className="rounded-xl border border-dashed border-white/10 p-10 text-center">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="mx-auto text-white/15 mb-4">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          <p className="text-sm text-white/40">No books saved offline yet.</p>
          <p className="text-xs text-white/25 mt-1.5">
            Open any book and tap <span className="text-white/40">Save offline</span> to read without internet.
          </p>
          <Link
            href="/"
            className="inline-flex items-center mt-5 px-4 py-2 rounded-lg text-xs font-medium border border-white/10 text-white/50 hover:text-white/70 hover:bg-white/5 transition-colors"
          >
            Browse books
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {books.map((book) => (
            <DownloadCard
              key={book.bookId}
              book={book}
              onRequestDelete={setPendingDelete}
            />
          ))}
        </div>
      )}

      {pendingDelete && (
        <ConfirmDeleteModal
          book={pendingDelete}
          onConfirm={handleConfirmDelete}
          onCancel={handleCancelDelete}
        />
      )}
    </section>
  );
}
