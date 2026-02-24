"use client";

import { Chapter, Annotation } from "@/lib/types";
import { readingTime } from "@/lib/utils";
import ChapterImage from "./ChapterImage";
import AnnotatedTerm from "./AnnotatedTerm";

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
}

/** Split text on quoted segments and style them differently. */
function renderWithQuotes(text: string, darkMode: boolean) {
  // Match straight "..." and curly \u201c...\u201d double quotes only
  const parts = text.split(/(\u201c[^\u201d]*\u201d|"[^"]*")/g);
  if (parts.length === 1) return text;
  const quoteColor = darkMode ? "rgb(186, 180, 160)" : "rgb(120, 90, 50)";
  return parts.map((part, i) => {
    if (/^[\u201c"]/.test(part)) {
      return (
        <span key={i} style={{ color: quoteColor, fontStyle: "italic" }}>
          {part}
        </span>
      );
    }
    return part;
  });
}

/** Render text with annotation highlights, then apply quote styling to non-annotated segments. */
function renderAnnotatedText(
  text: string,
  darkMode: boolean,
  terms: string[],
  glossary: Record<string, Annotation>,
) {
  if (terms.length === 0) return renderWithQuotes(text, darkMode);

  // Sort terms longest-first to avoid partial matches
  const sorted = [...terms].sort((a, b) => b.length - a.length);
  // Build regex: match any term (case-sensitive)
  const escaped = sorted.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`(${escaped.join("|")})`, "g");

  const parts = text.split(regex);
  if (parts.length === 1) return renderWithQuotes(text, darkMode);

  return parts.map((part, i) => {
    const annotation = glossary[part];
    if (annotation) {
      return <AnnotatedTerm key={i} term={part} annotation={annotation} darkMode={darkMode} />;
    }
    return <span key={i}>{renderWithQuotes(part, darkMode)}</span>;
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
}: ChapterContentProps) {
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
        {chapter.image && <ChapterImage src={chapter.image} alt={chapter.title} />}
      </div>

      {/* Chapter heading - used for IntersectionObserver tracking */}
      <div
        ref={(el) => registerRef(chapterIndex, el)}
        data-chapter={chapterIndex}
        className="text-center pt-12 pb-8 max-w-[720px] mx-auto px-5 sm:px-6"
      >
        <p
          className={`text-xs tracking-[0.25em] uppercase ${
            darkMode ? "text-white/30" : "text-black/30"
          }`}
        >
          Chapter {chapter.number}
        </p>
        <h2
          className={`text-2xl sm:text-3xl font-bold mt-2 ${
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
        className={`max-w-[720px] mx-auto px-5 sm:px-6 ${fontSizeMap[fontSize]}`}
        style={{ fontFamily: "var(--font-serif)" }}
      >
        {chapter.paragraphs.map((p, i) => (
          <p
            key={i}
            className={i > 0 ? "indent-[1.5em]" : ""}
            style={{ marginBottom: 0, marginTop: 0 }}
          >
            {chapterTerms && glossary
              ? renderAnnotatedText(p, darkMode, chapterTerms, glossary)
              : renderWithQuotes(p, darkMode)}
          </p>
        ))}
      </div>
    </article>
  );
}
