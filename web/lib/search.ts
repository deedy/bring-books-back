export type SearchDocumentKind = "anthology" | "book" | "author" | "chapter" | "term"
export type SearchImageShape = "circle" | "cover" | "landscape"

export interface SearchDocument {
  id: string
  kind: SearchDocumentKind
  title: string
  subtitle?: string
  description?: string
  url: string
  bookId?: string
  bookTitle?: string
  anthologyId?: string
  authorId?: string
  authorName?: string
  language?: string
  typeLabel?: string
  aliasesNormalized?: string[]
  imageUrl?: string
  imageAlt?: string
  imageShape?: SearchImageShape
  titleNormalized: string
  keywordsNormalized: string
  searchText: string
}

export interface SearchIndex {
  generatedAt: string
  documentCount: number
  documents: SearchDocument[]
}

const DIACRITICS_RE = /\p{Diacritic}/gu
const NON_WORD_RE = /[^a-z0-9]+/g

export function normalizeForSearch(value: string | null | undefined) {
  return (value ?? "")
    .normalize("NFKD")
    .replace(DIACRITICS_RE, "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(NON_WORD_RE, " ")
    .trim()
    .replace(/\s+/g, " ")
}

export function buildSearchText(parts: Array<string | null | undefined>) {
  return normalizeForSearch(parts.filter(Boolean).join(" "))
}

function kindBoost(kind: SearchDocumentKind) {
  switch (kind) {
    case "anthology":
      return 260
    case "book":
      return 180
    case "author":
      return 160
    case "chapter":
      return 120
    case "term":
      return 80
  }
}

export function runSearch(
  documents: SearchDocument[],
  query: string,
  limit = Number.POSITIVE_INFINITY,
) {
  const normalizedQuery = normalizeForSearch(query)
  if (normalizedQuery.length < 2) return []

  const terms = normalizedQuery.split(" ")

  return documents
    .map((document) => {
      if (!terms.every((term) => document.searchText.includes(term))) {
        return null
      }

      let score = kindBoost(document.kind)
      const aliases = document.aliasesNormalized ?? []

      if (document.titleNormalized === normalizedQuery) {
        score += 1200
      } else if (document.titleNormalized.startsWith(normalizedQuery)) {
        score += 900
      } else if (document.titleNormalized.includes(normalizedQuery)) {
        score += 600
      }

      if (aliases.some((alias) => alias === normalizedQuery)) {
        score += 1400
      } else if (aliases.some((alias) => alias.startsWith(normalizedQuery))) {
        score += 980
      } else if (aliases.some((alias) => alias.includes(normalizedQuery))) {
        score += 680
      }

      if (document.keywordsNormalized.startsWith(normalizedQuery)) {
        score += 220
      } else if (document.keywordsNormalized.includes(normalizedQuery)) {
        score += 120
      }

      for (const term of terms) {
        if (document.titleNormalized.includes(term)) {
          score += 40
        }
        if (document.keywordsNormalized.includes(term)) {
          score += 12
        }
      }

      return { document, score }
    })
    .filter((entry): entry is { document: SearchDocument; score: number } => !!entry)
    .sort((left, right) => {
      if (right.score !== left.score) return right.score - left.score
      if (left.document.title.length !== right.document.title.length) {
        return left.document.title.length - right.document.title.length
      }
      return left.document.title.localeCompare(right.document.title)
    })
    .slice(0, limit)
    .map(({ document }) => document)
}
