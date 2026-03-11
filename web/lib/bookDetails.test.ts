import { describe, expect, it } from "vitest";

import { buildGlossaryPreviewData } from "./bookDetails";
import type { AnnotationsData, Chapter } from "./types";

const chapters: Pick<Chapter, "id">[] = [
  { id: "ch-1" },
  { id: "ch-2" },
  { id: "ch-3" },
];

const annotations: AnnotationsData = {
  glossary: {
    Rama: {
      type: "character",
      description: "Prince of Ayodhya",
      image: "/rama.webp",
      aliases: ["Ram"],
    },
    Ayodhya: {
      type: "proper_noun",
      description: "Ancient city",
    },
    dharma: {
      type: "vocabulary",
      description: "Moral order",
    },
  },
  chapters: {
    "ch-1": ["Ram", "Ayodhya"],
    "ch-2": ["Rama", "dharma"],
    "ch-3": ["Rama"],
  },
};

describe("buildGlossaryPreviewData", () => {
  it("aggregates alias-aware preview cards and glossary terms", () => {
    const data = buildGlossaryPreviewData(annotations, chapters);

    expect(data.characters).toEqual([
      { name: "Rama", description: "Prince of Ayodhya", image: "/rama.webp" },
    ]);
    expect(data.totalCharacters).toBe(1);
    expect(data.totalProperNouns).toBe(1);
    expect(data.totalVocabulary).toBe(1);

    expect(data.glossaryTerms).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          name: "Rama",
          firstChapterIndex: 0,
          appearanceCount: 3,
        }),
        expect.objectContaining({
          name: "Ayodhya",
          firstChapterIndex: 0,
          appearanceCount: 1,
        }),
      ]),
    );
  });

  it("returns empty results when no annotations exist", () => {
    expect(buildGlossaryPreviewData(null, chapters)).toEqual({
      characters: [],
      properNouns: [],
      vocabulary: [],
      totalCharacters: 0,
      totalProperNouns: 0,
      totalVocabulary: 0,
      glossaryTerms: [],
    });
  });
});
