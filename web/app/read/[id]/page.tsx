import type { Metadata } from "next";
import { Suspense } from "react";
import { getCatalog } from "@/lib/data";
import { getReaderPayload } from "@/lib/readerData";
import ReaderLoader from "@/components/reader/ReaderLoader";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id);
  if (!book) return {};
  const author = catalog.authors.find((a) => a.id === book.authorId);
  const title = `Read ${book.title} by ${author?.name ?? "Unknown"}`;
  const description = `Read ${book.title} by ${author?.name ?? "Unknown"} — free English translation with illustrations`;
  const coverPng = `https://storage.googleapis.com/grandoldbooks-assets${book.coverImage.replace(".webp", ".png")}`;
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      images: [{ url: coverPng }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [coverPng],
    },
  };
}

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.books.filter((b) => b.type !== "anthology").map((book) => ({ id: book.id }));
}

export default async function ReadPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { id } = await params;
  const resolvedSearchParams = await searchParams;
  const languageParam = typeof resolvedSearchParams.language === "string"
    ? resolvedSearchParams.language
    : undefined;
  const resumeParam = typeof resolvedSearchParams.resume === "string"
    ? resolvedSearchParams.resume
    : undefined;
  const payload = await getReaderPayload(id, 0, languageParam, resumeParam);

  return (
    <Suspense fallback={
      <div className="fixed inset-0 bg-[#1a1a1a] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
      </div>
    }>
      <ReaderLoader
        accentColor={payload.accentColor}
        annotations={payload.annotations}
        authorName={payload.authorName}
        bookId={payload.bookId}
        bookTitle={payload.bookTitle}
        chapters={payload.chapters}
        coverImage={payload.coverImage}
        /* initialChapter omitted — ReaderView reads from Zustand store */
        isAuthenticated={payload.isAuthenticated}
        isOriginalActive={payload.isOriginalActive}
        originalScript={payload.originalScript}
        originalYear={payload.originalYear}
        resumeTarget={payload.resumeTarget}
        totalChapters={payload.totalChapters}
      />
    </Suspense>
  );
}
