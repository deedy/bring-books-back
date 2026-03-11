import { describe, expect, it } from "vitest";

import {
  buildOfflineCacheLookupUrls,
  buildOfflineBookUrl,
  buildOfflineGlossaryUrl,
  buildOfflinePayloadCacheUrl,
  buildOfflineReadUrl,
  buildOfflineWarmUrls,
  describeOfflineMode,
  resolveOfflineNavigationTarget,
  resolveOfflineMode,
  resolveOfflineTargetChapterIndex,
} from "./offlineUtils";
import type { Chapter } from "./types";

const chapters: Chapter[] = [
  {
    id: "c1",
    number: 1,
    title: "One",
    part: null,
    partName: null,
    image: "/c1.webp",
    wordCount: 100,
    paragraphs: [],
  },
  {
    id: "c2",
    number: 2,
    title: "Two",
    part: null,
    partName: null,
    image: "/c2.webp",
    wordCount: 100,
    paragraphs: [],
  },
  {
    id: "c3",
    number: 1,
    title: "Three",
    part: 2,
    partName: "Book Two",
    image: "/c3.webp",
    wordCount: 100,
    paragraphs: [],
  },
];

describe("offlineUtils", () => {
  it("resolves offline modes from language params", () => {
    expect(resolveOfflineMode(undefined)).toBe("english");
    expect(resolveOfflineMode("modern")).toBe("modern");
    expect(resolveOfflineMode("child")).toBe("child");
    expect(resolveOfflineMode("bengali")).toBe("original");
  });

  it("describes offline modes for UI", () => {
    expect(describeOfflineMode("english")).toBe("English");
    expect(describeOfflineMode("original", "bengali")).toBe("Original (bengali)");
  });

  it("builds offline cache and route URLs", () => {
    expect(buildOfflinePayloadCacheUrl("godan")).toBe("/__offline/books/godan.json");
    expect(buildOfflineBookUrl("godan")).toBe("/offline/books/godan");
    expect(buildOfflineGlossaryUrl("godan")).toBe("/offline/books/godan/glossary");
    expect(buildOfflineGlossaryUrl("godan", "?type=character")).toBe(
      "/offline/books/godan/glossary?type=character",
    );
    expect(buildOfflineReadUrl("godan")).toBe("/offline/read/godan");
    expect(buildOfflineReadUrl("godan", "2/two")).toBe("/offline/read/godan?target=2%2Ftwo");
    expect(buildOfflineWarmUrls("godan")).toEqual([
      "/downloads",
      "/offline-unavailable",
      "/offline/books/godan",
      "/offline/books/godan/glossary",
      "/offline/read/godan",
    ]);
  });

  it("maps live and offline routes to offline navigation targets", () => {
    expect(resolveOfflineNavigationTarget("/books/godan")).toBe("/offline/books/godan");
    expect(resolveOfflineNavigationTarget("/read/godan/2/two")).toBe(
      "/offline/read/godan?target=2%2Ftwo",
    );
    expect(resolveOfflineNavigationTarget("/books/godan/glossary", "?type=character")).toBe(
      "/offline/books/godan/glossary?type=character",
    );
    expect(resolveOfflineNavigationTarget("/offline/read/godan", "?target=2%2Ftwo")).toBe(
      "/offline/read/godan?target=2%2Ftwo",
    );
    expect(resolveOfflineNavigationTarget("/downloads")).toBe("/downloads");
    expect(resolveOfflineNavigationTarget("/authors/premchand")).toBeNull();
  });

  it("falls back from search variants to the base cached offline shell", () => {
    expect(buildOfflineCacheLookupUrls("/offline/read/godan?target=2%2Ftwo")).toEqual([
      "/offline/read/godan?target=2%2Ftwo",
      "/offline/read/godan",
    ]);
    expect(buildOfflineCacheLookupUrls("/offline/books/godan")).toEqual([
      "/offline/books/godan",
    ]);
  });

  it("resolves chapter indexes from offline target paths", () => {
    expect(resolveOfflineTargetChapterIndex(chapters, null)).toBe(0);
    expect(resolveOfflineTargetChapterIndex(chapters, "2")).toBe(1);
    expect(resolveOfflineTargetChapterIndex(chapters, "2/two")).toBe(1);
    expect(resolveOfflineTargetChapterIndex(chapters, "2/book-two/1/three")).toBe(2);
  });
});
