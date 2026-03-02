import type { Metadata } from "next";
import { getCatalog, getChapters } from "@/lib/data";
import { slugify, chapterPath } from "@/lib/utils";
import { redirect } from "next/navigation";
import ReaderLoader from "@/components/reader/ReaderLoader";

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
  const { chapters } = getChapters(id);

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
  const description = `Read ${book.title} by ${author?.name ?? "Unknown"} — free English translation with illustrations`;
  const coverPng = book.coverImage.replace(".webp", ".png");

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

export default async function ChapterRoutePage({
  params,
}: {
  params: Promise<{ id: string; path: string[] }>;
}) {
  const { id, path } = await params;
  const { chapters } = getChapters(id);

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
    redirect(`/read/${id}/${chapterPath(ch, clamped)}`);
  }

  // 2 segments → non-part book: [chapterId, chapterSlug]
  if (path.length === 2) {
    const num = parseInt(path[0], 10);
    const initialChapter = isNaN(num) ? 1 : num;
    return <ReaderLoader bookId={id} initialChapter={initialChapter} />;
  }

  // 4 segments → part book: [partNum, partSlug, chapterNum, chapterSlug]
  if (path.length === 4) {
    const partNum = parseInt(path[0], 10);
    const chapterNum = parseInt(path[2], 10);
    const idx = chapters.findIndex(
      (ch) => ch.part === partNum && ch.number === chapterNum,
    );
    const initialChapter = idx >= 0 ? idx + 1 : 1;
    return <ReaderLoader bookId={id} initialChapter={initialChapter} />;
  }

  // Fallback → first chapter
  const ch = chapters[0];
  redirect(`/read/${id}/${chapterPath(ch, 1)}`);
}
