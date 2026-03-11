import { describe, expect, it } from "vitest"
import {
  buildSearchText,
  normalizeForSearch,
  runSearch,
  type SearchDocument,
} from "./search"

function makeDoc(overrides: Partial<SearchDocument>): SearchDocument {
  const title = overrides.title ?? "Untitled"
  const titleNormalized = overrides.titleNormalized ?? normalizeForSearch(title)
  const keywordsNormalized = overrides.keywordsNormalized ?? ""
  return {
    id: overrides.id ?? titleNormalized,
    kind: overrides.kind ?? "book",
    title,
    url: overrides.url ?? "/",
    titleNormalized,
    keywordsNormalized,
    searchText: overrides.searchText ?? buildSearchText([titleNormalized, keywordsNormalized]),
    ...overrides,
  }
}

describe("search helpers", () => {
  it("normalizes punctuation and diacritics", () => {
    expect(normalizeForSearch("Maitreyi Dévi & Co.")).toBe("maitreyi devi and co")
  })

  it("ranks exact title matches above keyword-only matches", () => {
    const docs = [
      makeDoc({
        id: "book-1",
        kind: "book",
        title: "Devdas",
        keywordsNormalized: buildSearchText(["sarat chandra chattopadhyay", "bengali"]),
      }),
      makeDoc({
        id: "term-1",
        kind: "term",
        title: "Paro",
        keywordsNormalized: buildSearchText(["devdas", "character"]),
      }),
    ]

    expect(runSearch(docs, "devdas").map((doc) => doc.id)).toEqual(["book-1", "term-1"])
  })

  it("ranks an anthology exact alias match above repeated term matches", () => {
    const docs = [
      makeDoc({
        id: "anthology-1",
        kind: "anthology",
        title: "The Complete Adventures of Feluda",
        aliasesNormalized: ["feluda", "feluda samagra"],
        keywordsNormalized: buildSearchText(["feluda", "satyajit ray", "anthology"]),
      }),
      makeDoc({
        id: "term-1",
        kind: "term",
        title: "Feluda",
        keywordsNormalized: buildSearchText(["feluda in london", "character"]),
      }),
      makeDoc({
        id: "term-2",
        kind: "term",
        title: "Feluda",
        keywordsNormalized: buildSearchText(["the emperor's ring", "character"]),
      }),
    ]

    expect(runSearch(docs, "feluda").map((doc) => doc.id)).toEqual([
      "anthology-1",
      "term-1",
      "term-2",
    ])
  })

  it("requires all query terms to match somewhere in the document", () => {
    const docs = [
      makeDoc({
        id: "author-1",
        kind: "author",
        title: "Satyajit Ray",
      }),
      makeDoc({
        id: "book-1",
        kind: "book",
        title: "The Golden Fortress",
        keywordsNormalized: buildSearchText(["satyajit ray"]),
      }),
    ]

    expect(runSearch(docs, "satyajit fortress").map((doc) => doc.id)).toEqual(["book-1"])
  })
})
