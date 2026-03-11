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
  getKidChapters,
  getModernChapters,
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
  isKidActive: boolean;
  isModernActive: boolean;
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
  const modernData = getModernChapters(bookId);
  const kidData = getKidChapters(bookId);
  const { userId } = await auth();

  const requestedChapterIndex = Math.max(0, Math.min(initialChapterIndex, chaptersData.chapters.length - 1));
  const langLower = languageParam?.toLowerCase();
  const wantsOriginal = !!langLower && langLower !== "english" && langLower !== "modern" && langLower !== "child";
  const wantsModern = langLower === "modern";
  const wantsKid = langLower === "child";

  const book = catalog.books.find((entry) => entry.id === bookId);
  const author = book
    ? catalog.authors.find((entry) => entry.id === book.authorId)
    : null;

  const altChapterData = wantsKid && kidData
    ? kidData
    : wantsModern && modernData
      ? modernData
      : wantsOriginal && originalData
        ? originalData
        : null;

  const altChapterMap = altChapterData
    ? new Map(altChapterData.chapters.map((chapter) => [chapter.id, chapter]))
    : null;

  const resolvedChapters = chaptersData.chapters.map((chapter) => {
    const alt = altChapterMap?.get(chapter.id);
    if (!alt && (wantsModern || wantsKid)) {
      return { ...chapter, paragraphs: [] };
    }
    return mergeOriginalChapter(chapter, alt);
  });

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
    isKidActive: wantsKid && !!kidData,
    authorName: author?.name ?? "Unknown",
    bookId,
    bookTitle: bookMeta.title,
    chapters,
    coverImage: bookMeta.coverImage,
    isAuthenticated: isAuthenticated || isFreeBook,
    isModernActive: wantsModern && !!modernData,
    isOriginalActive: wantsOriginal && !!originalData,
    originalScript: wantsOriginal && originalData ? originalData.script : undefined,
    originalYear: bookMeta.originalYear,
    requestedChapterIndex,
    resumeTarget: isAuthenticated ? decodeResumeTarget(resumeParam) : null,
    totalChapters: bookMeta.totalChapters,
  };
}
