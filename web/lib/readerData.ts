import "server-only";

import { auth } from "@clerk/nextjs/server";
import {
  Annotation,
  Chapter,
  ChaptersData,
  OriginalChapter,
  ResumeTarget,
} from "./types";
import {
  buildPreviewParagraphs,
  decodeResumeTarget,
  previewGateFor,
} from "./readerAccess";
import {
  getAnnotations,
  getBookMeta,
  getCatalog,
  getChapters,
  getOriginalChapters,
} from "./data";

export const ANONYMOUS_PREVIEW_WORDS = 1000;

function mergeOriginalChapter(base: Chapter, original: OriginalChapter | undefined): Chapter {
  if (!original) return base;
  return {
    ...base,
    ...(original.title ? { title: original.title, slugTitle: base.title } : {}),
    paragraphs: original.paragraphs,
  };
}

function buildPreviewChapter(chapter: Chapter) {
  const preview = buildPreviewParagraphs(chapter.id, chapter.paragraphs, ANONYMOUS_PREVIEW_WORDS);
  if (!preview.gate) {
    return {
      ...chapter,
      accessMode: "full" as const,
      gate: null,
    };
  }
  return {
    ...chapter,
    paragraphs: preview.paragraphs,
    accessMode: "preview" as const,
    gate: preview.gate,
  };
}

function buildLockedChapter(chapter: Chapter) {
  return {
    ...chapter,
    paragraphs: [],
    accessMode: "locked" as const,
    gate: previewGateFor(chapter.id, 0, 0, ANONYMOUS_PREVIEW_WORDS),
  };
}

export interface ReaderPayload {
  accentColor: string;
  annotations?: {
    glossary: Record<string, Annotation>;
    chapters: Record<string, string[]>;
  };
  authorName: string;
  bookId: string;
  bookTitle: string;
  chapters: ChaptersData["chapters"];
  coverImage: string;
  isAuthenticated: boolean;
  isOriginalActive: boolean;
  originalScript?: string;
  originalYear: number;
  requestedChapterIndex: number;
  resumeTarget: ResumeTarget | null;
  totalChapters: number;
}

export async function getReaderPayload(
  bookId: string,
  initialChapterIndex: number,
  languageParam: string | null | undefined,
  resumeParam: string | null | undefined,
): Promise<ReaderPayload> {
  const catalog = getCatalog();
  const chaptersData = getChapters(bookId);
  const bookMeta = getBookMeta(bookId);
  const annotations = getAnnotations(bookId);
  const originalData = getOriginalChapters(bookId);
  const { userId } = await auth();

  const requestedChapterIndex = Math.max(0, Math.min(initialChapterIndex, chaptersData.chapters.length - 1));
  const wantsOriginal = !!languageParam && languageParam.toLowerCase() !== "english";

  const book = catalog.books.find((entry) => entry.id === bookId);
  const author = book
    ? catalog.authors.find((entry) => entry.id === book.authorId)
    : null;

  const originalChapterMap = wantsOriginal && originalData
    ? new Map(originalData.chapters.map((chapter) => [chapter.id, chapter]))
    : null;

  const resolvedChapters = chaptersData.chapters.map((chapter) =>
    mergeOriginalChapter(chapter, originalChapterMap?.get(chapter.id))
  );

  const FREE_BOOKS = new Set(["bhagavad-gita"]);
  const isAuthenticated = !!userId;
  const isFreeBook = FREE_BOOKS.has(bookId);
  const chapters = (isAuthenticated || isFreeBook)
    ? resolvedChapters.map((chapter) => ({
        ...chapter,
        accessMode: "full" as const,
        gate: null,
      }))
    : resolvedChapters.map((chapter, index) =>
        index === requestedChapterIndex ? buildPreviewChapter(chapter) : buildLockedChapter(chapter)
      );

  return {
    accentColor: bookMeta.accentColor,
    annotations: wantsOriginal ? undefined : annotations ?? undefined,
    authorName: author?.name ?? "Unknown",
    bookId,
    bookTitle: bookMeta.title,
    chapters,
    coverImage: bookMeta.coverImage,
    isAuthenticated: isAuthenticated || isFreeBook,
    isOriginalActive: wantsOriginal && !!originalData,
    originalScript: wantsOriginal && originalData ? originalData.script : undefined,
    originalYear: bookMeta.originalYear,
    requestedChapterIndex,
    resumeTarget: isAuthenticated ? decodeResumeTarget(resumeParam) : null,
    totalChapters: bookMeta.totalChapters,
  };
}
