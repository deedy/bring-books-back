import type { Metadata } from "next";
import { Suspense } from "react";
import { getCatalog, getAnnotations, getChapters } from "@/lib/data";
import GlossaryContent from "@/components/GlossaryContent";
import GlossaryHeaderBack from "@/components/GlossaryHeaderBack";
import OfflineRouteRedirect from "@/components/OfflineRouteRedirect";
import { buildGlossaryPreviewData } from "@/lib/bookDetails";

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
    alternates: { canonical: `/books/${id}/glossary` },
  };
}

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.books
    .filter((book) => getAnnotations(book.id) !== null)
    .map((book) => ({ id: book.id }));
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
  const { glossaryTerms: terms } = buildGlossaryPreviewData(annotations, chaptersData.chapters);

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <OfflineRouteRedirect bookId={id} kind="glossary" />
      <GlossaryHeaderBack bookId={id} bookTitle={book.title} />

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
