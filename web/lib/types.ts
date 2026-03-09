/** Shared fields between Book (catalog) and BookMeta (per-book meta.json). */
interface BookBase {
  id: string;
  title: string;
  transliteratedTitle: string;
  subtitle: string;
  authorId: string;
  coverImage: string;
  accentColor: string;
  genre: string[];
  originalLanguage: string;
  originalTitle: string;
  originalYear: number;
  yearEnd?: number;
  totalChapters: number;
  wordCount: number;
  summary: string;
  type?: "book" | "anthology";
  totalStories?: number;
  anthologyId?: string;
  storyNumber?: number;
  hasOriginalText?: boolean;
  originalScript?: string;
}

export interface Book extends BookBase {
  previewText: string;
  addedDate?: string;
}

export type ChapterParagraph = string | { text: string; type: "verse" };

export type ChapterAccessMode = "full" | "preview" | "locked";

export interface ResumeTarget {
  chapterId: string;
  paragraphIndex: number;
  wordOffset: number;
}

export interface ReaderGate {
  previewWords: number;
  paragraphIndex: number;
  wordOffset: number;
  anchorId: string;
}

export interface Author {
  id: string;
  name: string;
  image: string;
  years: string;
  bio: string;
  bookIds: string[];
}

export interface Catalog {
  books: Book[];
  authors: Author[];
}

export interface Chapter {
  id: string;
  number: number;
  title: string;
  part: number | null;
  partName: string | null;
  image: string;
  wordCount: number;
  paragraphs: ChapterParagraph[];
  subtitle?: string;
  summary?: string;
  accessMode?: ChapterAccessMode;
  gate?: ReaderGate | null;
}

export interface ChaptersData {
  chapters: Chapter[];
}

export type BookMeta = BookBase;

export interface ReadingProgress {
  currentChapter: number;
  scrollPercent: number;
  lastReadAt: string;
  finished: boolean;
}

export interface Annotation {
  type: "character" | "proper_noun" | "vocabulary";
  description: string;
  image?: string;
}

export interface AnnotationsData {
  glossary: Record<string, Annotation>;
  chapters: Record<string, string[]>;
}

export interface AnthologyData {
  storyBookIds: string[];
}

export interface OriginalChapter {
  id: string;
  title?: string;
  paragraphs: ChapterParagraph[];
}

export interface OriginalChaptersData {
  language: string;
  script: string;
  chapters: OriginalChapter[];
}
