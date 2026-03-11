"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import AnnotatedSummary from "@/components/AnnotatedSummary";
import BookCard from "@/components/BookCard";
import CharacterGrid from "@/components/CharacterGrid";
import ChapterList from "@/components/ChapterList";
import ShareButtons from "@/components/ShareButtons";
import { buildGlossaryPreviewData } from "@/lib/bookDetails";
import { loadOfflinePayload, removeBook } from "@/lib/offline";
import {
  buildOfflineGlossaryUrl,
  buildOfflineReadUrl,
  describeOfflineMode,
} from "@/lib/offlineUtils";
import { useReadingStore } from "@/lib/store";
import type { OfflineBookPayload, ReadingProgress } from "@/lib/types";
import { displayYear, pageCount, readingTime } from "@/lib/utils";

export default function OfflineBookPage() {
  const params = useParams<{ id: string }>();
  const bookId = params.id;
  const [payload, setPayload] = useState<OfflineBookPayload | null>(null);
  const [status, setStatus] = useState<"loading" | "ready" | "missing">("loading");

  useEffect(() => {
    let cancelled = false;
    loadOfflinePayload(bookId).then((data) => {
      if (cancelled) return;
      setPayload(data);
      setStatus(data ? "ready" : "missing");
    });
    return () => {
      cancelled = true;
    };
  }, [bookId]);

  const progress = useReadingStore((s) => s.getProgress(bookId));
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    if (useReadingStore.persist.hasHydrated()) {
      setHydrated(true);
    } else {
      useReadingStore.persist.onFinishHydration(() => setHydrated(true));
    }
  }, []);

  const glossaryData = useMemo(
    () => buildGlossaryPreviewData(payload?.bookAnnotations, payload?.chapters ?? []),
    [payload],
  );

  if (status === "loading") {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16 text-white/50">Loading offline book…</div>
    );
  }

  if (!payload) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-bold text-white">Offline book unavailable</h1>
        <p className="text-white/50 mt-4">
          This book is not currently stored on this device.
        </p>
        <Link
          href="/downloads"
          className="inline-flex items-center mt-6 px-4 py-2 rounded-lg border border-white/10 text-white/60 hover:text-white/80 hover:bg-white/5 transition-colors"
        >
          Back to downloads
        </Link>
      </div>
    );
  }

  const chaptersForList = payload.chapters.map(({ paragraphs, ...rest }) => rest);
  const {
    characters,
    properNouns,
    vocabulary,
    totalCharacters,
    totalProperNouns,
    totalVocabulary,
  } = glossaryData;

  const buildOfflineChapterHref = (targetPath: string, _languageParam?: string, hash?: string) =>
    `${buildOfflineReadUrl(payload.bookId, targetPath)}${hash ?? ""}`;

  return (
    <div className="pb-12">
      <div className="relative w-full h-[200px] md:h-[350px] -mt-4">
        <img
          src={payload.heroImage}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,10,11,0) 0%, rgba(10,10,11,0.15) 40%, rgba(10,10,11,0.7) 70%, rgba(10,10,11,1) 100%)",
          }}
        />
      </div>

      <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row gap-10 -mt-32 relative z-10">
        <div className="w-64 flex-shrink-0 mx-auto md:mx-0">
          <div
            className="relative aspect-[2/3] rounded-lg overflow-hidden"
            style={{
              boxShadow:
                "0 8px 30px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3), 0 0 60px rgba(0,0,0,0.25)",
            }}
          >
            <img
              src={payload.coverImage}
              alt={payload.title}
              loading="lazy"
              className="w-full h-full object-cover"
            />
            {payload.isNew && (
              <span className="absolute top-3 right-3 px-2.5 py-0.5 text-[11px] font-bold rounded bg-emerald-500/90 text-white backdrop-blur-sm uppercase tracking-wide">
                New
              </span>
            )}
          </div>
        </div>

        <div className="flex-1 drop-shadow-[0_2px_12px_rgba(0,0,0,0.6)]">
          <p className="text-xs uppercase tracking-[0.18em] text-white/35 mb-2">
            Offline{payload.mode !== "english" ? ` · ${describeOfflineMode(payload.mode, payload.languageParam)}` : ""}
          </p>
          <h1 className="text-3xl md:text-4xl font-bold text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]">
            {payload.title}
          </h1>
          <p className="text-lg text-white/60 mt-1">{payload.subtitle}</p>
          <Link
            href={`/authors/${payload.author.id}`}
            className="text-sm text-white/50 hover:text-white/80 transition-colors mt-2 inline-block"
          >
            by {payload.author.name}
          </Link>

          <div className="flex flex-wrap gap-2 mt-4">
            {payload.genre.map((genre) => (
              <span
                key={genre}
                className="px-3 py-1 text-xs font-medium rounded-full bg-white/10 text-white/70"
              >
                {genre}
              </span>
            ))}
          </div>

          <p className="text-sm text-white/40 mt-3 italic">
            {payload.title !== payload.transliteratedTitle
              ? `${payload.transliteratedTitle} (${payload.originalTitle})`
              : payload.originalTitle}
          </p>
          <div className="flex gap-6 mt-2 text-xs text-white/40">
            <span>Originally in {payload.originalLanguage}</span>
            <span>{displayYear(payload.originalYear, payload.yearEnd)}</span>
          </div>

          <div className="flex gap-6 mt-2 text-xs text-white/40">
            {payload.totalChapters > 1 && <span>{payload.totalChapters} chapters</span>}
            <span>{pageCount(payload.wordCount)} pages</span>
            <span>{readingTime(payload.wordCount)} read</span>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3" style={{ visibility: hydrated ? "visible" : "hidden" }}>
            <OfflineReadButton
              bookId={payload.bookId}
              accentColor={payload.accentColor}
              totalChapters={payload.totalChapters}
              progress={hydrated ? progress : null}
            />
            <Link
              href="/downloads"
              className="inline-flex items-center px-4 py-2 rounded-lg border border-white/10 text-sm font-medium text-white/55 hover:text-white/75 hover:bg-white/5 transition-colors"
            >
              Downloads
            </Link>
            <DeleteOfflineButton bookId={payload.bookId} />
          </div>

          <div className="mt-4">
            <ShareButtons url={`/books/${payload.bookId}`} title={`${payload.title} by ${payload.author.name}`} />
          </div>
        </div>
      </div>

      <section className="max-w-4xl mx-auto px-6 mt-16">
        <h2 className="text-xl font-bold text-white mb-4">About This Book</h2>
        {payload.bookAnnotations ? (
          <AnnotatedSummary summary={payload.summary} glossary={payload.bookAnnotations.glossary} />
        ) : (
          <p className="text-white/60 leading-relaxed">{payload.summary}</p>
        )}
      </section>

      {chaptersForList.length > 1 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">Chapters</h2>
          <ChapterList
            chapters={chaptersForList}
            bookId={payload.bookId}
            accentColor={payload.accentColor}
            buildHref={buildOfflineChapterHref}
          />
        </section>
      )}

      {characters.length > 0 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">Characters</h2>
          <CharacterGrid characters={characters} />
          {totalCharacters > 6 && (
            <Link
              href={buildOfflineGlossaryUrl(payload.bookId, "?type=character")}
              className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-4"
            >
              View all {totalCharacters} characters
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          )}
        </section>
      )}

      <section className="max-w-4xl mx-auto px-6 mt-16">
        <h2 className="text-xl font-bold text-white mb-4">About the Author</h2>
        <div className="flex gap-6 items-start">
          {payload.author.image ? (
            <Link href={`/authors/${payload.author.id}`} className="flex-shrink-0">
              <div className="w-20 h-20 rounded-full overflow-hidden">
                <img
                  src={payload.author.image}
                  alt={payload.author.name}
                  loading="lazy"
                  className="w-full h-full object-cover"
                />
              </div>
            </Link>
          ) : (
            <div className="w-20 h-20 rounded-full bg-white/5 flex-shrink-0" />
          )}
          <div>
            <Link
              href={`/authors/${payload.author.id}`}
              className="text-white font-semibold hover:text-white/80 transition-colors"
            >
              {payload.author.name}
            </Link>
            <p className="text-xs text-white/40 mt-0.5">{payload.author.years}</p>
            <p className="text-sm text-white/50 mt-2 leading-relaxed">
              {payload.author.bio.split("\n\n")[0]}
            </p>
          </div>
        </div>
      </section>

      {properNouns.length > 0 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-4">Places and Terms in this Book</h2>
          <div className="space-y-2">
            {properNouns.map((term) => (
              <p key={term.name} className="text-sm">
                <span className="font-medium text-white">{term.name}</span>
                <span className="text-white/40 ml-1.5">— {term.description}</span>
              </p>
            ))}
          </div>
          <Link
            href={buildOfflineGlossaryUrl(payload.bookId, "?type=proper_noun")}
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-3"
          >
            View all {totalProperNouns} places &amp; terms
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </section>
      )}

      {vocabulary.length > 0 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-4">Vocabulary</h2>
          <div className="space-y-2">
            {vocabulary.map((term) => (
              <p key={term.name} className="text-sm">
                <span className="font-medium text-white">{term.name}</span>
                <span className="text-white/40 ml-1.5">— {term.description}</span>
              </p>
            ))}
          </div>
          <Link
            href={buildOfflineGlossaryUrl(payload.bookId, "?type=vocabulary")}
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-3"
          >
            View all {totalVocabulary} vocabulary
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </section>
      )}

      {payload.otherBooks.length > 0 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">More by {payload.author.name}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {payload.otherBooks.map((book) => (
              <BookCard key={book.id} book={book} author={payload.author} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function OfflineReadButton({
  bookId,
  accentColor,
  totalChapters,
  progress,
}: {
  bookId: string;
  accentColor: string;
  totalChapters: number;
  progress?: ReadingProgress | null;
}) {
  let label = "Start Reading";
  if (progress) {
    if (progress.finished) {
      label = "Read Again";
    } else if (totalChapters === 1) {
      label = "Continue Reading";
    } else if (progress.currentSection != null) {
      label = `Continue Reading (Ch. ${progress.currentChapter + 1}, Sec. ${progress.currentSection})`;
    } else if (progress.currentChapter > 0) {
      label = `Continue Reading (Ch. ${progress.currentChapter + 1})`;
    }
  }

  const chapterTarget =
    progress && !progress.finished && progress.currentChapter > 0
      ? `${progress.currentChapter + 1}`
      : undefined;
  const href = buildOfflineReadUrl(bookId, chapterTarget);

  // Use <a> (full page load) to ensure ReaderView fully remounts and restores scroll position.
  return (
    <a
      href={href}
      className="inline-flex items-center px-5 py-3 rounded-lg text-white font-medium transition-opacity hover:opacity-90"
      style={{ backgroundColor: accentColor }}
    >
      {label}
    </a>
  );
}

function DeleteOfflineButton({ bookId }: { bookId: string }) {
  const router = useRouter();
  const handleDelete = async () => {
    await removeBook(bookId);
    router.push("/downloads");
  };

  return (
    <button
      onClick={handleDelete}
      className="p-2.5 rounded-lg border border-white/10 text-white/30 hover:text-red-400 hover:border-red-400/30 hover:bg-red-400/5 transition-colors"
      title="Remove offline download"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3 6 5 6 21 6" />
        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
        <path d="M10 11v6" />
        <path d="M14 11v6" />
      </svg>
    </button>
  );
}
