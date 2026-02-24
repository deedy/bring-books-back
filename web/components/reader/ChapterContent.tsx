"use client";

import { Chapter } from "@/lib/types";
import ChapterImage from "./ChapterImage";

interface ChapterContentProps {
  chapter: Chapter;
  chapterIndex: number;
  showPartDivider: boolean;
  registerRef: (idx: number, el: HTMLElement | null) => void;
  registerScrollTarget: (idx: number, el: HTMLElement | null) => void;
  darkMode: boolean;
  fontSize: "small" | "medium" | "large";
  isFirst: boolean;
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
          words &middot; {Math.max(1, Math.round(chapter.wordCount / 230))} min read
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
            {p}
          </p>
        ))}
      </div>
    </article>
  );
}
