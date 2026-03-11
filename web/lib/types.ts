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
  hasModernText?: boolean;
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
  /** English title preserved for URL slugs when reading in original language. */
  slugTitle?: string;
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
  aliases?: string[];
}

export interface AnnotationsData {
  glossary: Record<string, Annotation>;
  chapters: Record<string, string[]>;
}

/** Build a glossary that includes alias keys pointing to their canonical entry. */
export function resolveGlossary(glossary: Record<string, Annotation>): Record<string, Annotation> {
  const resolved: Record<string, Annotation> = { ...glossary };
  for (const entry of Object.values(glossary)) {
    if (entry.aliases) {
      for (const alias of entry.aliases) {
        if (!(alias in resolved)) {
          resolved[alias] = entry;
        }
      }
    }
  }
  return resolved;
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
