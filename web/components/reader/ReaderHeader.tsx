"use client";

import Link from "next/link";

interface ReaderHeaderProps {
  bookTitle: string;
  chapterLabel: string;
  visible: boolean;
  onTogglePicker: () => void;
  bookId: string;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  fontSize: "small" | "medium" | "large";
  onChangeFontSize: (size: "small" | "medium" | "large") => void;
  scrollMode: "paginated" | "infinite";
  onToggleScrollMode: () => void;
}

const fontSizes: Array<"small" | "medium" | "large"> = ["small", "medium", "large"];

export default function ReaderHeader({
  bookTitle,
  chapterLabel,
  visible,
  onTogglePicker,
  bookId,
  darkMode,
  onToggleDarkMode,
  fontSize,
  onChangeFontSize,
  scrollMode,
  onToggleScrollMode,
}: ReaderHeaderProps) {
  const nextSize = fontSizes[(fontSizes.indexOf(fontSize) + 1) % fontSizes.length];
  const sizeLabel = { small: "A", medium: "A", large: "A" }[fontSize];
  const sizeClass = { small: "text-xs", medium: "text-sm", large: "text-base" }[fontSize];

  const buttonClass = `px-2.5 py-1 rounded-md text-xs font-medium tracking-wide transition-colors border ${
    darkMode
      ? "border-white/20 text-white/70 hover:bg-white/10"
      : "border-black/20 text-black/70 hover:bg-black/10"
  }`;

  return (
    <header
      className={`fixed top-[3px] left-0 right-0 z-40 transition-transform duration-300 ${
        visible ? "translate-y-0" : "-translate-y-full"
      }`}
    >
      <div
        className={`${
          darkMode ? "bg-black/70" : "bg-white/70"
        } backdrop-blur-md`}
      >
        <div className="max-w-4xl mx-auto px-4 h-12 flex items-center justify-between relative">
          <div className="flex items-center gap-3">
            <button
              onClick={onTogglePicker}
              className={buttonClass}
              aria-label="Toggle table of contents"
            >
              Chapters
            </button>
          </div>

          <span className="absolute left-1/2 -translate-x-1/2 text-sm font-medium truncate max-w-[200px] sm:max-w-xs pointer-events-none">
            {bookTitle}
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={onToggleScrollMode}
              className={`p-2 rounded-lg transition-colors ${
                darkMode ? "hover:bg-white/10" : "hover:bg-black/10"
              }`}
              aria-label={scrollMode === "paginated" ? "Switch to infinite scroll" : "Switch to paginated"}
              title={scrollMode === "paginated" ? "Infinite scroll" : "Paginated"}
            >
              {scrollMode === "paginated" ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                </svg>
              )}
            </button>
            <button
              onClick={() => onChangeFontSize(nextSize)}
              className={`px-2 py-1 rounded transition-colors ${sizeClass} font-semibold ${
                darkMode ? "hover:bg-white/10" : "hover:bg-black/10"
              }`}
              aria-label={`Font size: ${fontSize}`}
              title={`Font size: ${fontSize}`}
            >
              {sizeLabel}
            </button>
            <button
              onClick={onToggleDarkMode}
              className={`p-2 rounded-lg transition-colors ${
                darkMode ? "hover:bg-white/10" : "hover:bg-black/10"
              }`}
              aria-label="Toggle dark mode"
            >
              {darkMode ? (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
              ) : (
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </button>
            <Link
              href={`/books/${bookId}`}
              className={buttonClass}
              aria-label="Go back to book details"
            >
              Back
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
