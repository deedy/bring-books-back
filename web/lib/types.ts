export interface Book {
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
  previewText: string;
  type?: "book" | "anthology";
  totalStories?: number;
  anthologyId?: string;
  storyNumber?: number;
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
  paragraphs: string[];
  summary?: string;
}

export interface ChaptersData {
  chapters: Chapter[];
}

export interface BookMeta {
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
}

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
