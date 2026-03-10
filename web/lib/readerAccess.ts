import { ChapterParagraph, ReaderGate, ResumeTarget } from "./types";

const WORD_PATTERN = /\S+\s*/g;

function getParagraphText(paragraph: ChapterParagraph) {
  return typeof paragraph === "string" ? paragraph : paragraph.text;
}

function getWordChunks(text: string) {
  return text.match(WORD_PATTERN) ?? [];
}

function sliceParagraph(paragraph: ChapterParagraph, visibleWords: number): ChapterParagraph {
  const chunks = getWordChunks(getParagraphText(paragraph));
  const nextText = chunks.slice(0, visibleWords).join("").trimEnd();
  if (typeof paragraph === "string") {
    return nextText;
  }
  return { ...paragraph, text: nextText };
}

export function createResumeAnchorId(
  chapterId: string,
  paragraphIndex: number,
  wordOffset: number,
) {
  return `resume-${chapterId}-${paragraphIndex}-${wordOffset}`;
}

export function encodeResumeTarget(target: ResumeTarget) {
  return `${target.chapterId}:${target.paragraphIndex}:${target.wordOffset}`;
}

export function decodeResumeTarget(value: string | null | undefined): ResumeTarget | null {
  if (!value) return null;
  const [chapterId, paragraphIndex, wordOffset] = value.split(":");
  const parsedParagraphIndex = Number.parseInt(paragraphIndex ?? "", 10);
  const parsedWordOffset = Number.parseInt(wordOffset ?? "", 10);
  if (!chapterId || Number.isNaN(parsedParagraphIndex) || Number.isNaN(parsedWordOffset)) {
    return null;
  }
  return {
    chapterId,
    paragraphIndex: parsedParagraphIndex,
    wordOffset: parsedWordOffset,
  };
}

export function previewGateFor(chapterId: string, paragraphIndex: number, wordOffset: number, previewWords: number): ReaderGate {
  return {
    previewWords,
    paragraphIndex,
    wordOffset,
    anchorId: createResumeAnchorId(chapterId, paragraphIndex, wordOffset),
  };
}

export function buildPreviewParagraphs(
  chapterId: string,
  paragraphs: ChapterParagraph[],
  previewWords: number,
) {
  const preview: ChapterParagraph[] = [];
  let remainingWords = previewWords;

  for (let i = 0; i < paragraphs.length; i += 1) {
    const paragraph = paragraphs[i];
    const chunks = getWordChunks(getParagraphText(paragraph));
    const chunkCount = chunks.length;

    if (chunkCount === 0) {
      preview.push(paragraph);
      continue;
    }

    if (remainingWords > chunkCount) {
      preview.push(paragraph);
      remainingWords -= chunkCount;
      continue;
    }

    if (remainingWords === chunkCount) {
      preview.push(paragraph);
      if (i === paragraphs.length - 1) {
        return { paragraphs: preview, gate: null };
      }
      return {
        paragraphs: preview,
        gate: previewGateFor(chapterId, i + 1, 0, previewWords),
      };
    }

    if (remainingWords > 0) {
      preview.push(sliceParagraph(paragraph, remainingWords));
      return {
        paragraphs: preview,
        gate: previewGateFor(chapterId, i, remainingWords, previewWords),
      };
    }

    return {
      paragraphs: preview,
      gate: previewGateFor(chapterId, i, 0, previewWords),
    };
  }

  return { paragraphs: preview, gate: null };
}
