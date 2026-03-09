import { describe, it, expect } from "vitest";
import {
  readingTime,
  readingTimeExact,
  readingTimeClock,
  pageCount,
  displayYear,
  slugify,
  chapterPath,
  getNewBookIds,
} from "./utils";
import type { Book } from "./types";

describe("readingTime", () => {
  it("returns minutes for short texts", () => {
    expect(readingTime(230)).toBe("1 min");
    expect(readingTime(460)).toBe("2 min");
    expect(readingTime(230 * 30)).toBe("30 min");
  });

  it("returns hours and minutes under 2h", () => {
    expect(readingTime(230 * 90)).toBe("1h 30min");
  });

  it("rounds to half hours between 2h and 10h", () => {
    expect(readingTime(230 * 150)).toBe("2½h");
    expect(readingTime(230 * 180)).toBe("3h");
    expect(readingTime(230 * 300)).toBe("5h");
  });

  it("rounds to whole hours above 10h", () => {
    expect(readingTime(230 * 660)).toBe("11h");
    expect(readingTime(230 * 720)).toBe("12h");
  });

  it("returns at least 1 min for tiny texts", () => {
    expect(readingTime(0)).toBe("1 min");
    expect(readingTime(5)).toBe("1 min");
  });
});

describe("readingTimeExact", () => {
  it("returns exact minutes for short texts", () => {
    expect(readingTimeExact(230 * 45)).toBe("45 min");
  });

  it("returns exact hours and minutes", () => {
    expect(readingTimeExact(230 * 155)).toBe("2h 35min");
  });

  it("returns clean hours when no remainder", () => {
    expect(readingTimeExact(230 * 120)).toBe("2h");
  });
});

describe("readingTimeClock", () => {
  it("formats as H:MM", () => {
    expect(readingTimeClock(230 * 5)).toBe("0:05");
    expect(readingTimeClock(230 * 65)).toBe("1:05");
    expect(readingTimeClock(230 * 120)).toBe("2:00");
  });
});

describe("pageCount", () => {
  it("rounds to nearest page", () => {
    expect(pageCount(250)).toBe(1);
    expect(pageCount(500)).toBe(2);
    expect(pageCount(375)).toBe(2);
  });
});

describe("displayYear", () => {
  it("formats a single year", () => {
    expect(displayYear(1965)).toBe("1965");
  });

  it("formats a year range", () => {
    expect(displayYear(1965, 1992)).toBe("1965\u20131992");
  });

  it("treats same start and end as single year", () => {
    expect(displayYear(1965, 1965)).toBe("1965");
  });

  it("handles BC years", () => {
    expect(displayYear(-300)).toBe("300 BC");
  });

  it("handles BC year range", () => {
    expect(displayYear(-300, -200)).toBe("300 BC\u2013200 BC");
  });
});

describe("slugify", () => {
  it("lowercases and replaces spaces with hyphens", () => {
    expect(slugify("Hello World")).toBe("hello-world");
  });

  it("strips special characters", () => {
    expect(slugify("The Emperor's Ring")).toBe("the-emperor-s-ring");
  });

  it("strips leading/trailing hyphens", () => {
    expect(slugify("--hello--")).toBe("hello");
  });

  it("collapses multiple separators", () => {
    expect(slugify("a   b   c")).toBe("a-b-c");
  });
});

describe("chapterPath", () => {
  it("returns sequential path for non-part chapters", () => {
    const ch = { title: "The Beginning", number: 1, part: null, partName: null };
    expect(chapterPath(ch, 1)).toBe("1/the-beginning");
  });

  it("returns part-based path for part chapters", () => {
    const ch = { title: "The Journey", number: 3, part: 2, partName: "Book Two" };
    expect(chapterPath(ch, 5)).toBe("2/book-two/3/the-journey");
  });
});

describe("getNewBookIds", () => {
  const makeBook = (id: string, addedDate?: string): Book => ({
    id,
    title: id,
    transliteratedTitle: id,
    subtitle: "",
    authorId: "a",
    coverImage: "",
    accentColor: "",
    genre: [],
    originalLanguage: "en",
    originalTitle: "",
    originalYear: 2000,
    totalChapters: 1,
    wordCount: 1000,
    summary: "",
    previewText: "",
    addedDate,
  });

  it("returns books added within last 14 days", () => {
    const today = new Date().toISOString().slice(0, 10);
    const books = [makeBook("new", today), makeBook("old", "2020-01-01"), makeBook("none")];
    const ids = getNewBookIds(books);
    expect(ids.has("new")).toBe(true);
    expect(ids.has("old")).toBe(false);
    expect(ids.has("none")).toBe(false);
  });

  it("returns empty set when no books have dates", () => {
    const books = [makeBook("a"), makeBook("b")];
    expect(getNewBookIds(books).size).toBe(0);
  });
});
