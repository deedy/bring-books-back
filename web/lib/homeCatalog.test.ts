import { describe, expect, it } from "vitest";

import { buildHomeBrowseModel } from "./homeCatalog";
import type { Book } from "./types";

function makeBook(overrides: Partial<Book> & Pick<Book, "id" | "title">): Book {
  const { id, title, ...rest } = overrides;
  return {
    id,
    title,
    transliteratedTitle: title,
    subtitle: "",
    authorId: "author-1",
    coverImage: "/cover.webp",
    accentColor: "#000000",
    genre: [],
    originalLanguage: "Bengali",
    originalTitle: title,
    originalYear: 1900,
    totalChapters: 1,
    wordCount: 10_000,
    summary: "",
    previewText: "",
    ...rest,
  };
}

describe("buildHomeBrowseModel", () => {
  it("builds themed default sections in curated order", () => {
    const books = [
      makeBook({ id: "mrinalini", title: "Mrinalini" }),
      makeBook({ id: "ramayana", title: "Ramayana" }),
      makeBook({ id: "feluda", title: "Feluda" }),
      makeBook({ id: "discovery-of-india", title: "Discovery of India" }),
      makeBook({ id: "godan", title: "Godan" }),
      makeBook({ id: "brothers-karamazov", title: "The Brothers Karamazov" }),
      makeBook({ id: "mahabharata", title: "Mahabharata" }),
      makeBook({ id: "maitreyi", title: "Bengal Nights" }),
      makeBook({ id: "autobiography-of-a-yogi", title: "Autobiography of a Yogi" }),
      makeBook({ id: "pather-panchali", title: "Pather Panchali" }),
      makeBook({ id: "bhagavad-gita", title: "Bhagavad Gita" }),
      makeBook({ id: "devdas", title: "Devdas" }),
      makeBook({ id: "crime-and-punishment", title: "Crime and Punishment" }),
      makeBook({ id: "baeesween-sadi", title: "The Twenty-Second Century" }),
      makeBook({ id: "samskara", title: "Samskara" }),
      makeBook({ id: "panchatantra", title: "The Panchatantra" }),
      makeBook({ id: "ghare-baire", title: "The Home and the World" }),
      makeBook({ id: "byomkesh", title: "Byomkesh" }),
      makeBook({ id: "barrister-parvateesam", title: "Barrister Parvateesam" }),
      makeBook({ id: "matira-manisha", title: "Man of the Soil" }),
    ];

    const model = buildHomeBrowseModel({
      books,
      langFilter: "all",
      sortField: "default",
      sortDir: "asc",
    });

    expect(model.mode).toBe("sectioned");
    if (model.mode !== "sectioned") return;

    expect(model.sections.map((section) => section.id)).toEqual([
      "epics-worlds",
      "russian-classics",
      "love-memory",
      "society-family",
      "mystery-conscience",
      "ideas-journeys",
    ]);
    expect(model.sections[0].books.map((book) => book.id)).toEqual([
      "mahabharata",
      "ramayana",
      "bhagavad-gita",
      "panchatantra",
    ]);
    expect(model.sections[1].books.map((book) => book.id)).toEqual([
      "crime-and-punishment",
      "brothers-karamazov",
    ]);
    expect(model.sections[2].books.map((book) => book.id)).toEqual([
      "devdas",
      "mrinalini",
      "ghare-baire",
      "maitreyi",
    ]);
    expect(model.sections[3].books.map((book) => book.id)).toEqual([
      "pather-panchali",
      "godan",
      "samskara",
      "matira-manisha",
    ]);
    expect(model.sections[4].books.map((book) => book.id)).toEqual([
      "feluda",
      "byomkesh",
    ]);
    expect(model.sections[5].books.map((book) => book.id)).toEqual([
      "discovery-of-india",
      "autobiography-of-a-yogi",
      "baeesween-sadi",
      "barrister-parvateesam",
    ]);
  });

  it("uses genre heuristics for books not in the curated theme map", () => {
    const books = [
      makeBook({ id: "mahabharata", title: "Mahabharata" }),
      makeBook({ id: "ramayana", title: "Ramayana" }),
      makeBook({ id: "bhagavad-gita", title: "Bhagavad Gita" }),
      makeBook({ id: "panchatantra", title: "The Panchatantra" }),
      makeBook({ id: "feluda", title: "Feluda" }),
      makeBook({ id: "byomkesh", title: "Byomkesh" }),
      makeBook({ id: "crime-and-punishment", title: "Crime and Punishment" }),
      makeBook({
        id: "custom-psychological",
        title: "Custom Psychological",
        genre: ["Psychological Fiction"],
        originalYear: 1910,
      }),
    ];

    const model = buildHomeBrowseModel({
      books,
      langFilter: "all",
      sortField: "default",
      sortDir: "asc",
    });

    expect(model.mode).toBe("flat");
    if (model.mode !== "flat") return;

    // Falls back to flat because russian-classics has only 1 book (crime-and-punishment),
    // which is below MIN_SECTION_BOOKS threshold.
    expect(model.books.map((book) => book.id)).toEqual([
      "mahabharata",
      "ramayana",
      "bhagavad-gita",
      "panchatantra",
      "crime-and-punishment",
      "feluda",
      "byomkesh",
      "custom-psychological",
    ]);
  });

  it("falls back to a flat grid when default sections would be too sparse", () => {
    const books = [
      makeBook({ id: "mahabharata", title: "Mahabharata", originalLanguage: "Sanskrit" }),
      makeBook({ id: "devdas", title: "Devdas", originalLanguage: "Bengali" }),
      makeBook({ id: "feluda", title: "Feluda", originalLanguage: "Bengali" }),
      makeBook({ id: "discovery-of-india", title: "Discovery of India", originalLanguage: "English" }),
    ];

    const model = buildHomeBrowseModel({
      books,
      langFilter: "Bengali",
      sortField: "default",
      sortDir: "asc",
    });

    expect(model).toEqual({
      mode: "flat",
      books: [books[1], books[2]],
    });
  });

  it("sorts by addedDate descending for recent sort", () => {
    const books = [
      makeBook({ id: "old", title: "Old Book", addedDate: "2026-01-01" }),
      makeBook({ id: "new", title: "New Book", addedDate: "2026-03-01" }),
      makeBook({ id: "mid", title: "Mid Book", addedDate: "2026-02-01" }),
    ];

    const model = buildHomeBrowseModel({
      books,
      langFilter: "all",
      sortField: "recent",
      sortDir: "asc",
    });

    expect(model).toEqual({
      mode: "flat",
      books: [books[1], books[2], books[0]],
    });
  });

  it("returns a flat globally sorted list for year sorting", () => {
    const books = [
      makeBook({ id: "late", title: "Late", originalYear: 1950, addedDate: "2026-02-01" }),
      makeBook({ id: "early", title: "Early", originalYear: 1850, addedDate: "2026-02-01" }),
      makeBook({ id: "middle", title: "Middle", originalYear: 1900, addedDate: "2026-02-01" }),
    ];

    const model = buildHomeBrowseModel({
      books,
      langFilter: "all",
      sortField: "year",
      sortDir: "asc",
    });

    expect(model).toEqual({
      mode: "flat",
      books: [books[1], books[2], books[0]],
    });
  });

  it("returns a flat globally sorted list for length sorting with stable tie-breaks", () => {
    const books = [
      makeBook({ id: "older", title: "Older", wordCount: 100_000, addedDate: "2026-02-01" }),
      makeBook({ id: "newer", title: "Newer", wordCount: 100_000, addedDate: "2026-02-10" }),
      makeBook({ id: "short", title: "Short", wordCount: 50_000, addedDate: "2026-02-01" }),
    ];

    const model = buildHomeBrowseModel({
      books,
      langFilter: "all",
      sortField: "length",
      sortDir: "asc",
    });

    expect(model).toEqual({
      mode: "flat",
      books: [books[2], books[1], books[0]],
    });
  });
});
