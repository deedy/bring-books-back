import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

import { getAnnotations, getCatalog, getBookMeta } from "@/lib/data";
import { getReaderPayload } from "@/lib/readerData";
import { resolveOfflineMode } from "@/lib/offlineUtils";
import type { OfflineBookPayload } from "@/lib/types";
import { getNewBookIds } from "@/lib/utils";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  const { userId } = await auth();
  if (!userId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((entry) => entry.id === id);
  if (!book) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  if (book.type === "anthology") {
    return NextResponse.json({ error: "Anthologies are not supported for offline download yet" }, { status: 400 });
  }

  const author = catalog.authors.find((entry) => entry.id === book.authorId);
  const bookMeta = getBookMeta(id);
  const bookAnnotations = getAnnotations(id);
  const otherBooks = catalog.books.filter(
    (entry) => entry.authorId === book.authorId && entry.id !== book.id && !entry.anthologyId,
  );
  const languageParam = request.nextUrl.searchParams.get("language") ?? undefined;
  const payload = await getReaderPayload(id, 0, languageParam, undefined);
  const isNew = getNewBookIds(catalog.books).has(book.id);
  const heroImage =
    payload.chapters.length === 1 && payload.chapters[0].image
      ? payload.chapters[0].image
      : `/data/images/heroes/${id}.webp`;

  const assetUrls = new Set<string>();
  assetUrls.add(bookMeta.coverImage);
  assetUrls.add(heroImage);
  if (author?.image) assetUrls.add(author.image);

  for (const sibling of otherBooks) {
    assetUrls.add(sibling.coverImage);
  }

  for (const chapter of payload.chapters) {
    if (chapter.image) assetUrls.add(chapter.image);
  }

  for (const entry of Object.values(bookAnnotations?.glossary ?? {})) {
    if (entry.image) assetUrls.add(entry.image);
  }
  const offlinePayload: OfflineBookPayload = {
    bookId: id,
    title: bookMeta.title,
    subtitle: bookMeta.subtitle,
    transliteratedTitle: bookMeta.transliteratedTitle,
    originalTitle: bookMeta.originalTitle,
    summary: bookMeta.summary,
    genre: bookMeta.genre,
    wordCount: bookMeta.wordCount,
    yearEnd: bookMeta.yearEnd,
    isNew,
    author: author ?? {
      id: book.authorId,
      name: "Unknown",
      image: "",
      years: "",
      bio: "",
      bookIds: [],
    },
    otherBooks,
    authorName: author?.name ?? "Unknown",
    accentColor: bookMeta.accentColor,
    coverImage: bookMeta.coverImage,
    heroImage,
    originalLanguage: bookMeta.originalLanguage,
    originalYear: bookMeta.originalYear,
    originalScript: payload.originalScript,
    totalChapters: bookMeta.totalChapters,
    mode: resolveOfflineMode(languageParam),
    languageParam,
    isOriginalActive: payload.isOriginalActive,
    chapters: payload.chapters,
    bookAnnotations: bookAnnotations ?? undefined,
    annotations: payload.annotations,
    assetUrls: Array.from(assetUrls),
  };

  return NextResponse.json(offlinePayload, {
    headers: { "Cache-Control": "no-store" },
  });
}
