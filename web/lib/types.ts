export interface Book {
  id: string;
  title: string;
  subtitle: string;
  authorId: string;
  coverImage: string;
  accentColor: string;
  genre: string[];
  originalLanguage: string;
  originalTitle: string;
  originalYear: number;
  totalChapters: number;
  wordCount: number;
  summary: string;
  previewText: string;
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
}

export interface ChaptersData {
  chapters: Chapter[];
}

export interface BookMeta {
  id: string;
  title: string;
  subtitle: string;
  authorId: string;
  coverImage: string;
  accentColor: string;
  genre: string[];
  originalLanguage: string;
  originalTitle: string;
  originalYear: number;
  totalChapters: number;
  wordCount: number;
  summary: string;
}

export interface ReadingProgress {
  currentChapter: number;
  scrollPercent: number;
  lastReadAt: string;
  finished: boolean;
}
