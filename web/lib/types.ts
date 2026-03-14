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
  hasKidText?: boolean;
  hasNumberedVerses?: boolean;
  popularity?: number;
  originalScript?: string;
  /** When the original text language differs from originalLanguage (e.g. Hindi text for a Sanskrit original) */
  originalTextLanguage?: string;
}

export interface Book extends BookBase {
  previewText: string;
  addedDate?: string;
}

export type ChapterParagraph = string | { text: string; type: "verse" | "section_header" };

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

export interface SectionInfo {
  number: number;
  label: string;
  paragraphIndex: number;
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
  sections?: SectionInfo[];
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
  currentSection?: number | null;
}

export interface Annotation {
  type: "character" | "proper_noun" | "vocabulary" | "footnote";
  description: string;
  image?: string;
  aliases?: string[];
}

export interface AnnotationsData {
  glossary: Record<string, Annotation>;
  chapters: Record<string, string[]>;
}

export interface GlossaryPreviewCard {
  name: string;
  description: string;
  image?: string;
}

export interface GlossaryTerm {
  name: string;
  type: Annotation["type"];
  description: string;
  image?: string;
  aliases?: string[];
  firstChapterIndex: number;
  appearanceCount: number;
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
  sections?: SectionInfo[];
}

export interface OriginalChaptersData {
  language: string;
  script: string;
  chapters: OriginalChapter[];
}

export type OfflineMode = "english" | "original" | "modern" | "child";

export interface OfflineBookEntry {
  bookId: string;
  title: string;
  authorName: string;
  coverImage: string;
  accentColor: string;
  totalChapters: number;
  mode: OfflineMode;
  languageParam?: string;
  cachedAt: string;
  estimatedSizeMB?: number;
}

export interface OfflineBookPayload {
  bookId: string;
  title: string;
  subtitle: string;
  transliteratedTitle: string;
  originalTitle: string;
  summary: string;
  genre: string[];
  wordCount: number;
  yearEnd?: number;
  accentColor: string;
  coverImage: string;
  heroImage: string;
  originalLanguage: string;
  originalYear: number;
  originalScript?: string;
  totalChapters: number;
  mode: OfflineMode;
  languageParam?: string;
  isNew: boolean;
  author: Author;
  authorName: string;
  otherBooks: Book[];
  isOriginalActive: boolean;
  chapters: Chapter[];
  bookAnnotations?: AnnotationsData;
  annotations?: AnnotationsData;
  assetUrls: string[];
  estimatedSizeMB?: number;
}
