import type {
  AnnotationsData,
  Chapter,
  GlossaryPreviewCard,
  GlossaryTerm,
} from "./types";

export interface GlossaryPreviewData {
  characters: GlossaryPreviewCard[];
  properNouns: GlossaryPreviewCard[];
  vocabulary: GlossaryPreviewCard[];
  totalCharacters: number;
  totalProperNouns: number;
  totalVocabulary: number;
  glossaryTerms: GlossaryTerm[];
}

const EMPTY_GLOSSARY_DATA: GlossaryPreviewData = {
  characters: [],
  properNouns: [],
  vocabulary: [],
  totalCharacters: 0,
  totalProperNouns: 0,
  totalVocabulary: 0,
  glossaryTerms: [],
};

export function buildGlossaryPreviewData(
  annotations: AnnotationsData | null | undefined,
  chapters: Pick<Chapter, "id">[],
): GlossaryPreviewData {
  if (!annotations) return EMPTY_GLOSSARY_DATA;

  const chapterIds = chapters.map((chapter) => chapter.id);

  const aliasToCanon: Record<string, string> = {};
  for (const [name, annotation] of Object.entries(annotations.glossary)) {
    aliasToCanon[name] = name;
    if (annotation.aliases) {
      for (const alias of annotation.aliases) {
        aliasToCanon[alias] = name;
      }
    }
  }

  const glossaryTerms: GlossaryTerm[] = Object.entries(annotations.glossary).map(
    ([name, annotation]) => {
      let firstChapterIndex = chapterIds.length;
      let appearanceCount = 0;

      for (let i = 0; i < chapterIds.length; i += 1) {
        const chapterTerms = annotations.chapters[chapterIds[i]];
        if (!chapterTerms) continue;

        const found = chapterTerms.some((term) => aliasToCanon[term] === name);
        if (!found) continue;

        if (firstChapterIndex === chapterIds.length) firstChapterIndex = i;
        appearanceCount += 1;
      }

      return {
        name,
        type: annotation.type,
        description: annotation.description,
        image: annotation.image,
        aliases: annotation.aliases,
        firstChapterIndex,
        appearanceCount,
      };
    },
  );

  const buildTopList = (
    type: GlossaryTerm["type"],
  ): { items: GlossaryPreviewCard[]; total: number } => {
    const matching = glossaryTerms
      .filter((term) => term.type === type)
      .sort((a, b) => b.appearanceCount - a.appearanceCount || a.name.localeCompare(b.name));

    return {
      items: matching.slice(0, 6).map(({ name, description, image }) => ({
        name,
        description,
        image,
      })),
      total: matching.length,
    };
  };

  const characters = buildTopList("character");
  const properNouns = buildTopList("proper_noun");
  const vocabulary = buildTopList("vocabulary");

  return {
    characters: characters.items,
    properNouns: properNouns.items,
    vocabulary: vocabulary.items,
    totalCharacters: characters.total,
    totalProperNouns: properNouns.total,
    totalVocabulary: vocabulary.total,
    glossaryTerms,
  };
}
