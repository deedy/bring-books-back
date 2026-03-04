"use client";

import { Chapter, Annotation } from "@/lib/types";
import { readingTime } from "@/lib/utils";
import { SCRIPT_CONFIG } from "@/lib/scripts";
import ChapterImage from "./ChapterImage";
import AnnotatedTerm from "./AnnotatedTerm";

export interface QuoteHighlight {
  paragraphIndex: number;
  accentColor: string;
}

interface ChapterContentProps {
  chapter: Chapter;
  chapterIndex: number;
  showPartDivider: boolean;
  registerRef: (idx: number, el: HTMLElement | null) => void;
  registerScrollTarget: (idx: number, el: HTMLElement | null) => void;
  darkMode: boolean;
  fontSize: "small" | "medium" | "large";
  isFirst: boolean;
  chapterTerms?: string[];
  glossary?: Record<string, Annotation>;
  hideImage?: boolean;
  hideChapterHeading?: boolean;
  quoteHighlight?: QuoteHighlight;
  onHighlightRef?: (el: HTMLElement | null) => void;
  languageScript?: string;
}

/** Split text on quoted segments and style them differently. */
function renderWithQuotes(text: string, darkMode: boolean) {
  // Match: curly double \u201c...\u201d, straight double "...", curly single \u2018...\u2019
  // For curly singles: require closing \u2019 to be followed by non-letter (space, punctuation, EOL)
  // to distinguish closing quotes from apostrophes (he\u2019s, that\u2019s)
  const quotePattern = /(\u201c[^\u201d]*\u201d|"[^"]*"|\u2018[\s\S]*?\u2019(?=[^a-zA-Z]|$))/g;
  const result: (string | React.ReactElement)[] = [];
  let lastIndex = 0;
  let match;
  while ((match = quotePattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      result.push(text.slice(lastIndex, match.index));
    }
    const quoteColor = darkMode ? "rgb(186, 180, 160)" : "rgb(120, 90, 50)";
    result.push(
      <span key={match.index} style={{ color: quoteColor, fontStyle: "italic" }}>
        {match[0]}
      </span>
    );
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex === 0) return text;
  if (lastIndex < text.length) result.push(text.slice(lastIndex));
  return result;
}

/** Render text with annotation highlights + quote styling, handling quotes that span across annotations. */
function renderAnnotatedText(
  text: string,
  darkMode: boolean,
  terms: string[],
  glossary: Record<string, Annotation>,
) {
  if (terms.length === 0) return renderWithQuotes(text, darkMode);

  // Sort terms longest-first to avoid partial matches
  const sortedTerms = [...terms].sort((a, b) => b.length - a.length);
  const escaped = sortedTerms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`\\b(${escaped.join("|")})\\b`, "g");

  const parts = text.split(regex);
  if (parts.length === 1) return renderWithQuotes(text, darkMode);

  // Pre-compute quote ranges from the full original text so quotes
  // that get split by annotation terms are still detected
  const quoteRanges: [number, number][] = [];
  const quoteRegex = /\u201c[^\u201d]*\u201d|"[^"]*"|\u2018[\s\S]*?\u2019(?=[^a-zA-Z]|$)/g;
  let qm;
  while ((qm = quoteRegex.exec(text)) !== null) {
    quoteRanges.push([qm.index, qm.index + qm[0].length]);
  }

  function posInQuote(p: number) {
    return quoteRanges.some(([s, e]) => p >= s && p < e);
  }

  const quoteColor = darkMode ? "rgb(186, 180, 160)" : "rgb(120, 90, 50)";
  let pos = 0;

  return parts.map((part, i) => {
    const start = pos;
    const end = pos + part.length;
    pos = end;
    if (!part) return null;

    const annotation = glossary[part];
    if (annotation) {
      if (posInQuote(start)) {
        return (
          <span key={i} style={{ color: quoteColor, fontStyle: "italic" }}>
            <AnnotatedTerm term={part} annotation={annotation} darkMode={darkMode} />
          </span>
        );
      }
      return <AnnotatedTerm key={i} term={part} annotation={annotation} darkMode={darkMode} />;
    }

    // Non-annotated text: find quote boundaries that cross this fragment
    const breaks = [start];
    for (const [qs, qe] of quoteRanges) {
      if (qs > start && qs < end) breaks.push(qs);
      if (qe > start && qe < end) breaks.push(qe);
    }
    breaks.push(end);
    breaks.sort((a, b) => a - b);
    const unique = breaks.filter((v, j) => j === 0 || v !== breaks[j - 1]);

    if (unique.length === 2) {
      // No quote boundaries cross this fragment
      if (posInQuote(start)) {
        return (
          <span key={i} style={{ color: quoteColor, fontStyle: "italic" }}>
            {part}
          </span>
        );
      }
      return <span key={i}>{part}</span>;
    }

    // Fragment crosses quote boundaries — split into sub-segments
    return (
      <span key={i}>
        {unique.slice(0, -1).map((segStart, j) => {
          const segText = text.slice(segStart, unique[j + 1]);
          if (!segText) return null;
          if (posInQuote(segStart)) {
            return (
              <span key={j} style={{ color: quoteColor, fontStyle: "italic" }}>
                {segText}
              </span>
            );
          }
          return <span key={j}>{segText}</span>;
        })}
      </span>
    );
  });
}

const fontSizeMap = {
  small: "text-[16px] leading-[1.75]",
  medium: "text-[17px] leading-[1.75] sm:text-[18px]",
  large: "text-[19px] leading-[1.8] sm:text-[20px]",
};

export default function ChapterContent({
  chapter,
  chapterIndex,
  showPartDivider,
  registerRef,
  registerScrollTarget,
  darkMode,
  fontSize,
  isFirst,
  chapterTerms,
  glossary,
  hideImage,
  hideChapterHeading,
  quoteHighlight,
  onHighlightRef,
  languageScript,
}: ChapterContentProps) {
  const isIndicScript = !!languageScript && languageScript !== "Latin";
  const config = languageScript ? SCRIPT_CONFIG[languageScript] : undefined;
  const fontClass = config?.fontClass ?? "";
  return (
    <article className={`mb-16 ${isFirst ? "pt-16" : ""}`}>
      {/* Part divider */}
      {showPartDivider && chapter.partName && (
        <div className="text-center py-16">
          <div
            className={`inline-block border-t border-b ${
              darkMode ? "border-white/20" : "border-black/20"
            } py-4 px-8`}
          >
            <p
              className={`text-xs tracking-[0.3em] uppercase ${
                darkMode ? "text-white/40" : "text-black/40"
              }`}
            >
              Part {chapter.part}
            </p>
            <p
              className={`text-lg font-semibold mt-1 ${
                darkMode ? "text-white/70" : "text-black/70"
              }`}
              style={{ fontFamily: "var(--font-serif)" }}
            >
              {chapter.partName}
            </p>
          </div>
        </div>
      )}

      {/* Scroll target - includes chapter image so navigation scrolls image into view */}
      <div ref={(el) => registerScrollTarget(chapterIndex, el)}>
        {!hideImage && chapter.image && <ChapterImage src={chapter.image} alt={chapter.title} />}
      </div>

      {/* Chapter heading - used for IntersectionObserver tracking */}
      <div
        ref={(el) => registerRef(chapterIndex, el)}
        data-chapter={chapterIndex}
        className="text-center pt-12 pb-8 max-w-[720px] mx-auto px-5 sm:px-6"
      >
        {!hideChapterHeading && (
          <p
            className={`text-xs tracking-[0.25em] uppercase ${
              darkMode ? "text-white/30" : "text-black/30"
            }`}
          >
            Chapter {chapter.number}
          </p>
        )}
        <h2
          className={`text-2xl sm:text-3xl font-bold ${hideChapterHeading ? "" : "mt-2"} ${
            darkMode ? "text-white/90" : "text-black/90"
          }`}
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {chapter.title}
        </h2>
        <p
          className={`text-[11px] mt-3 tracking-wide ${
            darkMode ? "text-white/20" : "text-black/20"
          }`}
        >
          {chapter.wordCount >= 1000
            ? `${(chapter.wordCount / 1000).toFixed(1)}k`
            : chapter.wordCount}{" "}
          words &middot; {readingTime(chapter.wordCount)} read
        </p>
      </div>

      {/* Paragraphs */}
      <div
        className={`max-w-[720px] mx-auto px-5 sm:px-6 ${fontSizeMap[fontSize]} ${fontClass}`}
        style={{
          fontFamily: isIndicScript ? undefined : "var(--font-serif)",
          ...(isIndicScript && config ? { lineHeight: config.lineHeight } : {}),
        }}
      >
        {chapter.paragraphs.map((p, i) => {
          const isHighlighted = !languageScript && quoteHighlight?.paragraphIndex === i;
          return (
            <p
              key={i}
              data-p={i}
              ref={isHighlighted ? onHighlightRef : undefined}
              className={i > 0 ? "indent-[1.5em]" : ""}
              style={{
                marginBottom: 0,
                marginTop: 0,
                ...(isHighlighted
                  ? {
                      backgroundColor: quoteHighlight!.accentColor + "18",
                      borderLeft: `3px solid ${quoteHighlight!.accentColor}`,
                      paddingLeft: "1em",
                      paddingTop: "0.3em",
                      paddingBottom: "0.3em",
                      marginLeft: "-1.2em",
                      borderRadius: "0 4px 4px 0",
                    }
                  : undefined),
              }}
            >
              {chapterTerms && glossary
                ? renderAnnotatedText(p, darkMode, chapterTerms, glossary)
                : renderWithQuotes(p, darkMode)}
            </p>
          );
        })}
      </div>
    </article>
  );
}
