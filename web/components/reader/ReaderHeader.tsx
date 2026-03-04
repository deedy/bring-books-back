"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";

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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const nextSize = fontSizes[(fontSizes.indexOf(fontSize) + 1) % fontSizes.length];
  const sizeLabel = { small: "A", medium: "A", large: "A" }[fontSize];
  const sizeClass = { small: "text-xs", medium: "text-sm", large: "text-base" }[fontSize];

  // Close settings menu on outside click
  useEffect(() => {
    if (!settingsOpen) return;
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setSettingsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [settingsOpen]);

  const buttonClass = `px-2.5 py-1 rounded-md text-xs font-medium tracking-wide transition-colors border ${
    darkMode
      ? "border-white/20 text-white/70 hover:bg-white/10"
      : "border-black/20 text-black/70 hover:bg-black/10"
  }`;

  const menuItemClass = `flex items-center justify-between gap-4 w-full px-3 py-2.5 text-sm transition-colors rounded-md ${
    darkMode ? "hover:bg-white/10" : "hover:bg-black/5"
  }`;

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-transform duration-300 ${
        visible ? "translate-y-0" : "-translate-y-full"
      }`}
    >
      <div
        className={`backdrop-blur-xl border-b ${
          darkMode ? "bg-[#0a0a0a]/40 border-white/[0.06]" : "bg-white/40 border-black/[0.06]"
        }`}
        style={{ paddingTop: "env(safe-area-inset-top, 0px)" }}
      >
        <div className="max-w-4xl mx-auto px-4 h-12 flex items-center justify-between relative">
          <div className="flex items-center gap-2">
            <Link
              href={`/books/${bookId}`}
              className={`${buttonClass} inline-flex items-center gap-1`}
              aria-label="Go back to book details"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="15 18 9 12 15 6" />
              </svg>
              Back
            </Link>
          </div>

          <span className="absolute left-1/2 -translate-x-1/2 text-sm font-medium truncate max-w-[140px] sm:max-w-xs pointer-events-none">
            {bookTitle}
          </span>

          {/* Desktop: show all buttons inline */}
          <div className="hidden sm:flex items-center gap-2">
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
            <button
              onClick={onTogglePicker}
              className={buttonClass}
              aria-label="Toggle table of contents"
            >
              Chapters
            </button>
          </div>

          {/* Mobile: settings gear + chapters */}
          <div className="flex sm:hidden items-center gap-1" ref={menuRef}>
            <button
              onClick={() => setSettingsOpen(!settingsOpen)}
              className={`p-2 rounded-lg transition-colors ${
                darkMode ? "hover:bg-white/10" : "hover:bg-black/10"
              }`}
              aria-label="Settings"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="3" />
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
              </svg>
            </button>
            <button
              onClick={onTogglePicker}
              className={buttonClass}
              aria-label="Toggle table of contents"
            >
              Chapters
            </button>

            {/* Dropdown menu */}
            {settingsOpen && (
              <div
                className={`absolute top-full right-4 mt-1 w-52 rounded-lg border shadow-lg p-1.5 ${
                  darkMode
                    ? "bg-neutral-900 border-white/10"
                    : "bg-white border-black/10"
                }`}
              >
                <button
                  onClick={() => { onToggleScrollMode(); setSettingsOpen(false); }}
                  className={menuItemClass}
                >
                  <span>{scrollMode === "paginated" ? "Infinite scroll" : "Paginated"}</span>
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
                  onClick={() => { onChangeFontSize(nextSize); setSettingsOpen(false); }}
                  className={menuItemClass}
                >
                  <span>Font size: {fontSize}</span>
                  <span className={`${sizeClass} font-semibold`}>{sizeLabel}</span>
                </button>
                <button
                  onClick={() => { onToggleDarkMode(); setSettingsOpen(false); }}
                  className={menuItemClass}
                >
                  <span>{darkMode ? "Light mode" : "Dark mode"}</span>
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
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
