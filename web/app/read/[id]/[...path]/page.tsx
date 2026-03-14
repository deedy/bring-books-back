import type { Metadata } from "next";
import { Suspense } from "react";
import { getCatalog, getChapters } from "@/lib/data";
import { getReaderPayload } from "@/lib/readerData";
import { slugify, chapterPath } from "@/lib/utils";
import { notFound, redirect } from "next/navigation";
import OfflineRouteRedirect from "@/components/OfflineRouteRedirect";
import ReaderLoader from "@/components/reader/ReaderLoader";

export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string; path: string[] }>;
}): Promise<Metadata> {
  const { id, path } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id);
  if (!book) return {};
  const author = catalog.authors.find((a) => a.id === book.authorId);
  let chapters: Awaited<ReturnType<typeof getChapters>>["chapters"];
  try {
    chapters = getChapters(id).chapters;
  } catch {
    return {};
  }

  // Resolve chapter from path segments
  let chapterTitle = "";
  if (path.length === 2) {
    const num = parseInt(path[0], 10);
    const ch = chapters[isNaN(num) ? 0 : num - 1];
    if (ch) chapterTitle = ch.title;
  } else if (path.length === 4) {
    const partNum = parseInt(path[0], 10);
    const chapterNum = parseInt(path[2], 10);
    const ch = chapters.find((c) => c.part === partNum && c.number === chapterNum);
    if (ch) chapterTitle = ch.title;
  }

  const title = chapterTitle
    ? `${chapterTitle} — ${book.title}`
    : `Read ${book.title}`;
  const description = chapterTitle
    ? `Read "${chapterTitle}" from ${book.title} by ${author?.name ?? "Unknown"} — free English translation with illustrations`
    : `Read ${book.title} by ${author?.name ?? "Unknown"} — free English translation with illustrations`;
  const coverPng = `https://storage.googleapis.com/grandoldbooks-assets${book.coverImage.replace(".webp", ".png")}`;

  return {
    title,
    description,
    robots: "index, follow",
    authors: author ? [{ name: author.name, url: `/authors/${author.id}` }] : undefined,
    alternates: { canonical: `/read/${id}/${path.join("/")}` },
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

export async function generateStaticParams() {
  const catalog = getCatalog();
  const params: { id: string; path: string[] }[] = [];

  for (const book of catalog.books) {
    if (book.type === "anthology") continue;
    const { chapters } = getChapters(book.id);
    chapters.forEach((ch, idx) => {
      // Redirect shorthand: sequential index only
      params.push({ id: book.id, path: [String(idx + 1)] });

      // Full path with slugs
      if (ch.part != null && ch.partName) {
        params.push({
          id: book.id,
          path: [
            String(ch.part),
            slugify(ch.partName),
            String(ch.number),
            slugify(ch.title),
          ],
        });
      } else {
        params.push({
          id: book.id,
          path: [String(idx + 1), slugify(ch.title)],
        });
      }
    });
  }

  return params;
}

function BreadcrumbScript({ bookId, bookTitle, chapterTitle, path }: { bookId: string; bookTitle: string; chapterTitle: string; path: string[] }) {
  const breadcrumbLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://grandoldbooks.com/" },
      { "@type": "ListItem", position: 2, name: bookTitle, item: `https://grandoldbooks.com/books/${bookId}` },
      { "@type": "ListItem", position: 3, name: chapterTitle, item: `https://grandoldbooks.com/read/${bookId}/${path.join("/")}` },
    ],
  };
  const chapterLd = {
    "@context": "https://schema.org",
    "@type": "Chapter",
    name: chapterTitle,
    isPartOf: {
      "@type": "Book",
      name: bookTitle,
      url: `https://grandoldbooks.com/books/${bookId}`,
    },
    url: `https://grandoldbooks.com/read/${bookId}/${path.join("/")}`,
  };
  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }} />
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(chapterLd) }} />
    </>
  );
}

export default async function ChapterRoutePage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string; path: string[] }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { id, path } = await params;
  const resolvedSearchParams = await searchParams;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id);
  if (!book) notFound();
  const bookTitle = book.title;
  const { chapters } = getChapters(id);
  const languageParam = typeof resolvedSearchParams.language === "string"
    ? resolvedSearchParams.language
    : undefined;
  const resumeParam = typeof resolvedSearchParams.resume === "string"
    ? resolvedSearchParams.resume
    : undefined;

  // 1 segment → redirect shorthand (sequential index)
  if (path.length === 1) {
    const num = parseInt(path[0], 10);
    const clamped =
      isNaN(num) || num > chapters.length
        ? chapters.length
        : num < 1
        ? 1
        : num;
    const ch = chapters[clamped - 1];
    const qsParts: string[] = [];
    if (languageParam) qsParts.push(`language=${encodeURIComponent(languageParam)}`);
    const verseParam = typeof resolvedSearchParams.verse === "string" ? resolvedSearchParams.verse : undefined;
    if (verseParam) qsParts.push(`verse=${encodeURIComponent(verseParam)}`);
    const qs = qsParts.length > 0 ? `?${qsParts.join("&")}` : "";
    redirect(`/read/${id}/${chapterPath(ch, clamped)}${qs}`);
  }

  // 2 segments → non-part book: [chapterId, chapterSlug]
  if (path.length === 2) {
    const num = parseInt(path[0], 10);
    const initialChapter = isNaN(num) ? 1 : num;
    const ch = chapters[isNaN(num) ? 0 : num - 1];
    const payload = await getReaderPayload(id, initialChapter - 1, languageParam, resumeParam);
    return (
      <>
        <OfflineRouteRedirect bookId={id} kind="read" target={path.join("/")} />
        <BreadcrumbScript bookId={id} bookTitle={bookTitle} chapterTitle={ch?.title ?? `Chapter ${num}`} path={path} />
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
            initialChapter={payload.requestedChapterIndex + 1}
            isAuthenticated={payload.isAuthenticated}
            isOriginalActive={payload.isOriginalActive}
            originalScript={payload.originalScript}
            originalYear={payload.originalYear}
            resumeTarget={payload.resumeTarget}
            totalChapters={payload.totalChapters}
            hasNumberedVerses={payload.hasNumberedVerses}
          />
        </Suspense>
      </>
    );
  }

  // 4 segments → part book: [partNum, partSlug, chapterNum, chapterSlug]
  if (path.length === 4) {
    const partNum = parseInt(path[0], 10);
    const chapterNum = parseInt(path[2], 10);
    const idx = chapters.findIndex(
      (ch) => ch.part === partNum && ch.number === chapterNum,
    );
    const initialChapter = idx >= 0 ? idx + 1 : 1;
    const ch = idx >= 0 ? chapters[idx] : chapters[0];
    const payload = await getReaderPayload(id, initialChapter - 1, languageParam, resumeParam);
    return (
      <>
        <OfflineRouteRedirect bookId={id} kind="read" target={path.join("/")} />
        <BreadcrumbScript bookId={id} bookTitle={bookTitle} chapterTitle={ch?.title ?? `Chapter ${chapterNum}`} path={path} />
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
            initialChapter={payload.requestedChapterIndex + 1}
            isAuthenticated={payload.isAuthenticated}
            isOriginalActive={payload.isOriginalActive}
            originalScript={payload.originalScript}
            originalYear={payload.originalYear}
            resumeTarget={payload.resumeTarget}
            totalChapters={payload.totalChapters}
            hasNumberedVerses={payload.hasNumberedVerses}
          />
        </Suspense>
      </>
    );
  }

  // Fallback → first chapter
  const ch = chapters[0];
  redirect(`/read/${id}/${chapterPath(ch, 1)}`);
}
