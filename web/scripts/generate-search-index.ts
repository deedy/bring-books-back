import fs from "fs"
import path from "path"
import {
  buildSearchText,
  normalizeForSearch,
  type SearchDocument,
  type SearchIndex,
} from "../lib/search"
import { chapterPath } from "../lib/utils"

interface CatalogBook {
  id: string
  title: string
  transliteratedTitle: string
  subtitle: string
  authorId: string
  coverImage: string
  genre: string[]
  originalLanguage: string
  originalTitle: string
  summary: string
  type?: "book" | "anthology"
  anthologyId?: string
}

interface CatalogAuthor {
  id: string
  name: string
  years: string
  bio: string
  image: string
}

interface ChapterData {
  id: string
  title: string
  slugTitle?: string
  number: number
  part: number | null
  partName: string | null
  image?: string
  subtitle?: string
  summary?: string
}

interface AnnotationEntry {
  type: "character" | "proper_noun" | "vocabulary" | "place" | "term"
  description: string
  image?: string
  aliases?: string[]
}

const ROOT = process.cwd()
const PUBLIC_DIR = path.join(ROOT, "public", "data")
const SERVER_DIR = path.join(ROOT, "server-data", "books")
const OUTPUT_DIR = path.join(PUBLIC_DIR, "search")
const OUTPUT_FILE = path.join(OUTPUT_DIR, "index.json")

function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T
}

function authorDescription(bio: string) {
  return bio.split("\n\n")[0]?.trim() ?? ""
}

function typeLabel(type: AnnotationEntry["type"]) {
  switch (type) {
    case "character":
      return "Character"
    case "proper_noun":
      return "Place or Term"
    case "vocabulary":
      return "Vocabulary"
    case "place":
      return "Place"
    case "term":
      return "Cultural Term"
  }
}

const catalog = readJson<{ books: CatalogBook[]; authors: CatalogAuthor[] }>(
  path.join(PUBLIC_DIR, "catalog.json"),
)

const authorsById = new Map(catalog.authors.map((author) => [author.id, author]))

const documents: SearchDocument[] = []

for (const author of catalog.authors) {
  const authorBooks = catalog.books
    .filter((book) => book.authorId === author.id)
    .map((book) => book.title)

  const titleNormalized = normalizeForSearch(author.name)
  const aliasesNormalized = [normalizeForSearch(author.id)].filter(Boolean)
  const keywordsNormalized = buildSearchText([author.years, ...authorBooks])

  documents.push({
    id: `author:${author.id}`,
    kind: "author",
    title: author.name,
    subtitle: author.years,
    description: authorDescription(author.bio),
    url: `/authors/${author.id}`,
    authorId: author.id,
    aliasesNormalized,
    imageUrl: author.image,
    imageAlt: author.name,
    imageShape: "circle",
    titleNormalized,
    keywordsNormalized,
    searchText: buildSearchText([titleNormalized, ...aliasesNormalized, keywordsNormalized]),
  })
}

for (const book of catalog.books) {
  const author = authorsById.get(book.authorId)
  const titleNormalized = normalizeForSearch(book.title)
  const aliasesNormalized = [
    normalizeForSearch(book.id),
    normalizeForSearch(book.transliteratedTitle),
    normalizeForSearch(book.originalTitle),
  ].filter(Boolean)
  const keywordsNormalized = buildSearchText([
    book.id,
    author?.name,
    book.originalTitle,
    book.transliteratedTitle,
    book.originalLanguage,
    ...book.genre,
  ])

  documents.push({
    id: `book:${book.id}`,
    kind: book.type === "anthology" ? "anthology" : "book",
    title: book.title,
    subtitle: author?.name,
    description: book.summary,
    url: `/books/${book.id}`,
    bookId: book.id,
    anthologyId: book.anthologyId,
    authorId: book.authorId,
    authorName: author?.name,
    language: book.originalLanguage,
    aliasesNormalized,
    imageUrl: book.coverImage,
    imageAlt: book.title,
    imageShape: "cover",
    titleNormalized,
    keywordsNormalized,
    searchText: buildSearchText([
      titleNormalized,
      ...aliasesNormalized,
      keywordsNormalized,
      book.summary,
    ]),
  })
}

for (const book of catalog.books) {
  const chaptersPath = path.join(SERVER_DIR, book.id, "chapters.json")
  if (!fs.existsSync(chaptersPath)) continue

  const author = authorsById.get(book.authorId)
  const chapterData = readJson<{ chapters: ChapterData[] }>(chaptersPath)

  chapterData.chapters.forEach((chapter, index) => {
    const titleNormalized = normalizeForSearch(chapter.title)
    const aliasesNormalized = [normalizeForSearch(chapter.slugTitle)].filter(Boolean)
    const keywordsNormalized = buildSearchText([
      book.title,
      book.id,
      author?.name,
      chapter.partName,
      chapter.subtitle,
      chapter.summary,
      `chapter ${chapter.number}`,
    ])
    const chapterImage = chapter.image || book.coverImage

    documents.push({
      id: `chapter:${book.id}:${chapter.id}`,
      kind: "chapter",
      title: chapter.title,
      subtitle: `${book.title} · Chapter ${chapter.number}`,
      description: chapter.summary ?? chapter.subtitle,
      url: `/read/${book.id}/${chapterPath(chapter, index + 1)}`,
      bookId: book.id,
      bookTitle: book.title,
      authorId: book.authorId,
      authorName: author?.name,
      aliasesNormalized,
      imageUrl: chapterImage,
      imageAlt: chapter.title,
      imageShape: chapterImage === chapter.image ? "landscape" : "cover",
      titleNormalized,
      keywordsNormalized,
      searchText: buildSearchText([titleNormalized, ...aliasesNormalized, keywordsNormalized]),
    })
  })
}

for (const book of catalog.books) {
  const annotationsPath = path.join(PUBLIC_DIR, "books", book.id, "annotations.json")
  if (!fs.existsSync(annotationsPath)) continue

  const author = authorsById.get(book.authorId)
  const annotations = readJson<{ glossary: Record<string, AnnotationEntry> }>(annotationsPath)

  for (const [term, annotation] of Object.entries(annotations.glossary)) {
    const titleNormalized = normalizeForSearch(term)
    const aliasesNormalized = (annotation.aliases ?? [])
      .map((alias) => normalizeForSearch(alias))
      .filter(Boolean)
    const keywordsNormalized = buildSearchText([
      book.title,
      book.id,
      author?.name,
      typeLabel(annotation.type),
      ...(annotation.aliases ?? []),
      annotation.description,
    ])

    documents.push({
      id: `term:${book.id}:${term}`,
      kind: "term",
      title: term,
      subtitle: `${book.title} · ${typeLabel(annotation.type)}`,
      description: annotation.description,
      url: `/books/${book.id}/glossary?q=${encodeURIComponent(term)}`,
      bookId: book.id,
      bookTitle: book.title,
      authorId: book.authorId,
      authorName: author?.name,
      typeLabel: typeLabel(annotation.type),
      aliasesNormalized,
      imageUrl: annotation.image ?? book.coverImage,
      imageAlt: term,
      imageShape: annotation.image ? "circle" : "cover",
      titleNormalized,
      keywordsNormalized,
      searchText: buildSearchText([titleNormalized, ...aliasesNormalized, keywordsNormalized]),
    })
  }
}

const payload: SearchIndex = {
  generatedAt: new Date().toISOString(),
  documentCount: documents.length,
  documents,
}

fs.mkdirSync(OUTPUT_DIR, { recursive: true })
fs.writeFileSync(OUTPUT_FILE, JSON.stringify(payload))

console.log(`Generated search index with ${documents.length} documents`)
