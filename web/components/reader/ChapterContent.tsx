"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Chapter, Annotation, SectionInfo, resolveGlossary } from "@/lib/types";
import type { ResumeTarget } from "@/lib/types";
import { readingTimeExact, pageCount } from "@/lib/utils";
import { SCRIPT_CONFIG } from "@/lib/scripts";
import ChapterImage from "./ChapterImage";
import AnnotatedTerm from "./AnnotatedTerm";

export interface QuoteHighlight {
  paragraphIndex: number;
  accentColor: string;
}

interface ChapterContentProps {
  authLinks?: {
    returnUrl: string;
    signInUrl: string;
    signUpUrl: string;
  };
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
  overlapsImage?: boolean;
  onAuthIntent?: (returnUrl: string) => void;
  quoteHighlight?: QuoteHighlight;
  resumeTarget?: ResumeTarget | null;
  onHighlightRef?: (el: HTMLElement | null) => void;
  languageScript?: string;
  accentColor?: string;
  bookTitle?: string;
  allGlossary?: Record<string, Annotation>;
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

function CtaTagline({
  darkMode,
  bookTitle,
  allGlossary,
}: {
  darkMode: boolean;
  bookTitle?: string;
  allGlossary?: Record<string, Annotation>;
}) {
  const [character, setCharacter] = useState<{ name: string; image: string } | null>(null);
  const [seconds, setSeconds] = useState("3.5");
  useEffect(() => {
    setSeconds((Math.floor(Math.random() * 31 + 20) / 10).toFixed(1));
    if (allGlossary) {
      const chars = Object.entries(allGlossary)
        .filter(([, a]) => a.type === "character" && a.image)
        .slice(0, 6);
      if (chars.length > 0) {
        const pick = chars[Math.floor(Math.random() * chars.length)];
        setCharacter({ name: pick[0], image: pick[1].image! });
      }
    }
  }, [allGlossary]);

  const colorClass = darkMode ? "text-white/40" : "text-black/35";

  return (
    <div className={`mt-4 max-w-sm mx-auto text-center`}>
      <p className={`text-sm leading-relaxed ${colorClass}`}>
        Logging in only takes {seconds} seconds. It lets you save progress and highlight.
        {character && bookTitle && (
          <>
            {" "}<span className={darkMode ? "text-white/60" : "text-black/50"}>{character.name}</span> from{" "}
            <span className={`italic ${darkMode ? "text-white/60" : "text-black/50"}`}>{bookTitle}</span> is waiting.
          </>
        )}
      </p>
      {character && (
        <img
          src={character.image}
          alt={character.name}
          className="max-w-[200px] rounded-lg mx-auto mt-3 border border-white/10"
        />
      )}
    </div>
  );
}

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
  overlapsImage,
  authLinks,
  onAuthIntent,
  quoteHighlight,
  resumeTarget,
  onHighlightRef,
  languageScript,
  accentColor,
  bookTitle,
  allGlossary,
}: ChapterContentProps) {
  const isIndicScript = !!languageScript && languageScript !== "Latin";
  const config = languageScript ? SCRIPT_CONFIG[languageScript] : undefined;
  const fontClass = config?.fontClass ?? "";
  const resolvedGlossary = glossary ? resolveGlossary(glossary) : undefined;

  // Build section index map for fast lookup
  const sectionMap = useMemo(() => {
    const map = new Map<number, SectionInfo>();
    if (chapter.sections) {
      for (const sec of chapter.sections) {
        map.set(sec.paragraphIndex, sec);
      }
    }
    return map;
  }, [chapter.sections]);
  const isPreviewChapter = chapter.accessMode === "preview";
  const isLockedChapter = chapter.accessMode === "locked";
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
        className="text-center pt-12 pb-8 max-w-[720px] mx-auto px-5 sm:px-6 relative z-10"
      >
        {hideChapterHeading ? (
          <p
            className={`text-xs tracking-[0.25em] uppercase ${
              darkMode ? "text-white/50" : "text-black/30"
            }`}
            style={overlapsImage ? { textShadow: "0 0 6px rgba(0,0,0,1), 0 0 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7)" } : undefined}
          >
            Short Story
          </p>
        ) : (
          <p
            className={`text-xs tracking-[0.25em] uppercase ${
              darkMode ? "text-white/50" : "text-black/30"
            }`}
            style={overlapsImage ? { textShadow: "0 0 6px rgba(0,0,0,1), 0 0 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7)" } : undefined}
          >
            Chapter {chapter.number}
          </p>
        )}
        <h2
          className={`text-2xl sm:text-3xl font-bold mt-2 ${
            darkMode ? "text-white" : "text-black/90"
          }`}
          style={{
            fontFamily: "var(--font-serif)",
            ...(overlapsImage ? { textShadow: "0 2px 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.6)" } : {}),
          }}
        >
          {chapter.title}
        </h2>
        {chapter.subtitle && (
          <p
            className={`text-[15px] mt-2 italic ${
              darkMode ? "text-white/60" : "text-black/50"
            }`}
            style={{
              fontFamily: "var(--font-serif)",
              letterSpacing: "0.02em",
              ...(overlapsImage ? { textShadow: "0 1px 12px rgba(0,0,0,0.9), 0 0 30px rgba(0,0,0,0.7)" } : {}),
            }}
          >
            {chapter.subtitle}
          </p>
        )}
        <p
          className={`text-[11px] mt-3 tracking-wide ${
            darkMode ? "text-white/50" : "text-black/20"
          }`}
          style={overlapsImage ? { textShadow: "0 0 6px rgba(0,0,0,1), 0 0 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7)" } : undefined}
        >
          {readingTimeExact(chapter.wordCount)} read &middot; {pageCount(chapter.wordCount)} pages
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
        {chapter.paragraphs.map((rawP, i) => {
          // Section marker: render as styled divider
          const section = sectionMap.get(i);
          if (section) {
            return (
              <div
                key={i}
                id={`section-${section.number}`}
                data-section={section.number}
                data-p={i}
                className="my-10 text-center"
              >
                <div
                  className={`inline-block border-t border-b py-2 px-6 ${
                    darkMode ? "border-white/15" : "border-black/10"
                  }`}
                >
                  <span
                    className={`text-xs tracking-[0.2em] uppercase ${
                      darkMode ? "text-white/40" : "text-black/35"
                    }`}
                    style={{ fontVariant: "small-caps", letterSpacing: "0.15em" }}
                  >
                    {section.label}
                  </span>
                </div>
              </div>
            );
          }

          const isVerse = typeof rawP === "object" && rawP.type === "verse";
          const p = typeof rawP === "string" ? rawP : rawP.text;
          const isHighlighted = !languageScript && quoteHighlight?.paragraphIndex === i;
          return (
            <div key={i}>
              {resumeTarget?.chapterId === chapter.id && resumeTarget.paragraphIndex === i && (
                <div
                  id={`resume-${resumeTarget.chapterId}-${resumeTarget.paragraphIndex}-${resumeTarget.wordOffset}`}
                  className="h-0"
                />
              )}
              <p
                data-p={i}
                ref={isHighlighted ? onHighlightRef : undefined}
                className={i > 0 && !isVerse ? "indent-[1.5em]" : ""}
                style={{
                  marginBottom: isVerse ? "0.8em" : 0,
                  marginTop: isVerse ? "0.8em" : 0,
                  ...(isVerse
                    ? {
                        fontStyle: "italic",
                        paddingLeft: "1.5em",
                        borderLeft: `2px solid ${darkMode ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.12)"}`,
                        opacity: 0.88,
                      }
                    : {}),
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
                {chapterTerms && resolvedGlossary
                  ? renderAnnotatedText(p, darkMode, chapterTerms, resolvedGlossary)
                  : renderWithQuotes(p, darkMode)}
              </p>
            </div>
          );
        })}

        {authLinks && (isPreviewChapter || isLockedChapter) && (
          <>
            {/* Fade overlay on last visible text */}
            {isPreviewChapter && (
              <div
                className="relative -mt-80 h-80 pointer-events-none"
                style={{
                  background: `linear-gradient(to bottom, transparent 0%, ${darkMode ? "#1a1a1a" : "#fafafa"}30 35%, ${darkMode ? "#1a1a1a" : "#fafafa"}90 65%, ${darkMode ? "#1a1a1a" : "#fafafa"} 100%)`,
                }}
              />
            )}

            {/* Sign-in CTA */}
            <div
              id={chapter.gate?.anchorId}
              className={`text-center ${isPreviewChapter ? "mt-0" : "mt-6"} py-6`}
            >
              <CtaTagline darkMode={darkMode} bookTitle={bookTitle} allGlossary={allGlossary} />
              <div className="flex items-center justify-center mt-5">
                <Link
                  href={authLinks.signInUrl}
                  onClick={() => onAuthIntent?.(authLinks.returnUrl)}
                  className="inline-flex items-center justify-center rounded-xl px-10 py-4 text-base font-bold transition-all hover:scale-[1.02] hover:shadow-lg bg-[#22c55e] text-white shadow-md shadow-green-500/20"
                >
                  Sign in to read for free
                </Link>
              </div>
            </div>
          </>
        )}
      </div>
    </article>
  );
}
