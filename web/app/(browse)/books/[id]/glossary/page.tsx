import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";
import { getCatalog, getAnnotations, getChapters } from "@/lib/data";
import GlossaryContent from "@/components/GlossaryContent";

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.books
    .filter((book) => getAnnotations(book.id) !== null)
    .map((book) => ({ id: book.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id);
  if (!book) return {};
  return {
    title: `Glossary - ${book.title}`,
    description: `Characters, places, and vocabulary from ${book.title}`,
  };
}

export interface GlossaryTerm {
  name: string;
  type: "character" | "proper_noun" | "vocabulary";
  description: string;
  image?: string;
  firstChapterIndex: number;
  appearanceCount: number;
}

export default async function GlossaryPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id)!;
  const annotations = getAnnotations(id);

  if (!annotations) {
    return (
      <div className="max-w-4xl mx-auto px-6 py-12">
        <p className="text-white/60">No glossary available for this book.</p>
      </div>
    );
  }

  const chaptersData = getChapters(id);
  const chapterIds = chaptersData.chapters.map((ch) => ch.id);

  // Pre-compute sort keys for each term
  const terms: GlossaryTerm[] = Object.entries(annotations.glossary).map(
    ([name, annotation]) => {
      let firstChapterIndex = chapterIds.length;
      let appearanceCount = 0;
      for (let i = 0; i < chapterIds.length; i++) {
        const chTerms = annotations.chapters[chapterIds[i]];
        if (chTerms?.includes(name)) {
          if (firstChapterIndex === chapterIds.length) firstChapterIndex = i;
          appearanceCount++;
        }
      }
      return {
        name,
        type: annotation.type,
        description: annotation.description,
        image: annotation.image,
        firstChapterIndex,
        appearanceCount,
      };
    }
  );

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      {/* Breadcrumb — back to reader (restores saved position) */}
      <div className="mb-8">
        <Link
          href={`/read/${id}`}
          className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          Back to reading
        </Link>
      </div>

      <h1 className="text-3xl font-bold text-white mb-2">Glossary</h1>
      <p className="text-white/50 text-sm mb-10">
        {terms.length} entries from {book.title}
      </p>

      <Suspense>
        <GlossaryContent terms={terms} />
      </Suspense>
    </div>
  );
}
