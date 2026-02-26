"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { Chapter, AnnotationsData } from "@/lib/types";
import { useReadingStore } from "@/lib/store";
import ReaderHeader from "./ReaderHeader";
import ProgressBar from "./ProgressBar";
import ChapterContent from "./ChapterContent";
import ChapterImage from "./ChapterImage";
import ChapterPicker from "./ChapterPicker";
import { chapterPath } from "@/lib/utils";

interface ReaderViewProps {
  bookId: string;
  bookTitle: string;
  accentColor: string;
  chapters: Chapter[];
  totalChapters: number;
  initialChapter?: number;
  annotations?: AnnotationsData;
}

export default function ReaderView({
  bookId,
  bookTitle,
  accentColor,
  chapters,
  totalChapters,
  initialChapter,
  annotations,
}: ReaderViewProps) {
  const updateProgress = useReadingStore((s) => s.updateProgress);
  const savedProgress = useReadingStore((s) => s.getProgress(bookId));
  const scrollMode = useReadingStore((s) => s.scrollMode);
  const setScrollMode = useReadingStore((s) => s.setScrollMode);

  const [currentIndex, setCurrentIndex] = useState(() => {
    if (initialChapter !== undefined && initialChapter >= 1 && initialChapter <= chapters.length) {
      return initialChapter - 1;
    }
    return savedProgress?.currentChapter ?? 0;
  });
  const [showPicker, setShowPicker] = useState(false);
  const [headerVisible, setHeaderVisible] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [fontSize, setFontSize] = useState<"small" | "medium" | "large">("medium");
  const [chapterProgress, setChapterProgress] = useState(0);
  const lastScrollY = useRef(0);

  // Refs for infinite scroll mode
  const chapterHeadingRefs = useRef<Map<number, HTMLElement>>(new Map());
  const chapterScrollTargetRefs = useRef<Map<number, HTMLElement>>(new Map());
  // Suppress observer updates while programmatically scrolling
  const suppressObserverRef = useRef(false);

  const chapter = chapters[currentIndex];
  const prevChapter = currentIndex > 0 ? chapters[currentIndex - 1] : null;

  // Build chapter URL path
  const chapterUrl = useCallback(
    (idx: number) => {
      const ch = chapters[idx];
      return `/read/${bookId}/${chapterPath(ch, idx + 1)}`;
    },
    [bookId, chapters]
  );

  // Navigate to chapter by index
  const goToChapter = useCallback(
    (idx: number) => {
      if (idx < 0 || idx >= chapters.length) return;
      setShowPicker(false);

      if (scrollMode === "infinite") {
        // Scroll to the chapter's position
        const target = chapterScrollTargetRefs.current.get(idx) ?? chapterHeadingRefs.current.get(idx);
        if (target) {
          suppressObserverRef.current = true;
          setCurrentIndex(idx);
          target.scrollIntoView({ behavior: "auto", block: "start" });
          // Offset for the header
          window.scrollBy(0, -60);
          window.history.replaceState({}, "", chapterUrl(idx));
          setTimeout(() => { suppressObserverRef.current = false; }, 200);
        }
      } else {
        setCurrentIndex(idx);
        window.scrollTo({ top: 0, behavior: "auto" });
        window.history.replaceState({}, "", chapterUrl(idx));
      }
    },
    [chapters.length, chapterUrl, scrollMode]
  );

  // Toggle scroll mode
  const handleToggleScrollMode = useCallback(() => {
    const newMode = scrollMode === "paginated" ? "infinite" : "paginated";
    setScrollMode(newMode);

    if (newMode === "infinite") {
      // Will scroll to current chapter after render via effect below
    } else {
      // Switching to paginated — currentIndex is already set by the observer
      window.scrollTo({ top: 0, behavior: "auto" });
    }
  }, [scrollMode, setScrollMode]);

  // After switching to infinite mode, scroll to the current chapter
  useEffect(() => {
    if (scrollMode === "infinite") {
      // Small delay to let all chapters render
      const timer = setTimeout(() => {
        const target = chapterScrollTargetRefs.current.get(currentIndex) ?? chapterHeadingRefs.current.get(currentIndex);
        if (target) {
          suppressObserverRef.current = true;
          target.scrollIntoView({ behavior: "auto", block: "start" });
          window.scrollBy(0, -60);
          setTimeout(() => { suppressObserverRef.current = false; }, 200);
        }
      }, 50);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scrollMode]);

  // Sync URL and save progress whenever chapter changes
  useEffect(() => {
    updateProgress(bookId, { currentChapter: currentIndex });
    window.history.replaceState({}, "", chapterUrl(currentIndex));
  }, [bookId, currentIndex, updateProgress, chapterUrl]);

  // IntersectionObserver for infinite scroll — detect which chapter is visible
  useEffect(() => {
    if (scrollMode !== "infinite") return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (suppressObserverRef.current) return;

        // Find the topmost visible chapter heading
        let topEntry: IntersectionObserverEntry | null = null;
        for (const entry of entries) {
          if (entry.isIntersecting) {
            if (!topEntry || entry.boundingClientRect.top < topEntry.boundingClientRect.top) {
              topEntry = entry;
            }
          }
        }

        if (topEntry) {
          const idx = Number(topEntry.target.getAttribute("data-chapter"));
          if (!isNaN(idx)) {
            setCurrentIndex(idx);
          }
        }
      },
      {
        rootMargin: "-10% 0px -70% 0px",
        threshold: 0,
      }
    );

    // Observe all chapter heading refs
    chapterHeadingRefs.current.forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, [scrollMode, chapters.length]);

  // Scroll tracking: header visibility + chapter progress
  useEffect(() => {
    const handleScroll = () => {
      const y = window.scrollY;
      setHeaderVisible(y < 50 || y < lastScrollY.current);
      lastScrollY.current = y;

      if (scrollMode === "infinite") {
        // Chapter progress: track within the current chapter heading element
        const headingEl = chapterHeadingRefs.current.get(currentIndex);
        const nextHeadingEl = chapterHeadingRefs.current.get(currentIndex + 1);
        if (headingEl) {
          const chapterTop = headingEl.getBoundingClientRect().top + window.scrollY;
          const chapterBottom = nextHeadingEl
            ? nextHeadingEl.getBoundingClientRect().top + window.scrollY
            : document.documentElement.scrollHeight;
          const chapterHeight = chapterBottom - chapterTop;
          if (chapterHeight > 0) {
            const progress = ((y - chapterTop + window.innerHeight * 0.3) / chapterHeight) * 100;
            setChapterProgress(Math.max(0, Math.min(100, progress)));
          }
        }
      } else {
        // Paginated: whole-page progress
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (scrollHeight > 0) {
          setChapterProgress(Math.min(100, (y / scrollHeight) * 100));
        }
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [scrollMode, currentIndex]);

  // Keyboard nav: left/right arrows (paginated only)
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (scrollMode !== "paginated") return;
      if (e.key === "ArrowLeft" && currentIndex > 0) {
        goToChapter(currentIndex - 1);
      } else if (e.key === "ArrowRight" && currentIndex < chapters.length - 1) {
        goToChapter(currentIndex + 1);
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [currentIndex, chapters.length, goToChapter, scrollMode]);

  // Ref registration callbacks
  const registerRef = useCallback((idx: number, el: HTMLElement | null) => {
    if (el) {
      chapterHeadingRefs.current.set(idx, el);
    } else {
      chapterHeadingRefs.current.delete(idx);
    }
  }, []);

  const registerScrollTarget = useCallback((idx: number, el: HTMLElement | null) => {
    if (el) {
      chapterScrollTargetRefs.current.set(idx, el);
    } else {
      chapterScrollTargetRefs.current.delete(idx);
    }
  }, []);

  const overallProgress = scrollMode === "infinite"
    ? (() => {
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        return scrollHeight > 0 ? Math.min(100, (lastScrollY.current / scrollHeight) * 100) : 0;
      })()
    : ((currentIndex + chapterProgress / 100) / totalChapters) * 100;

  const nextChapter = currentIndex < chapters.length - 1 ? chapters[currentIndex + 1] : null;

  const bgColor = darkMode ? "#1a1a1a" : "#fafafa";
  const textColor = darkMode ? "#e5e5e5" : "#1a1a1a";

  const chapterLabel = chapter
    ? chapter.partName
      ? `Pt ${chapter.part}: ${chapter.partName} · Ch. ${chapter.number}: ${chapter.title}`
      : `Ch. ${chapter.number}: ${chapter.title}`
    : "";

  // Determine which chapters show part dividers
  const showPartDividerForChapter = (idx: number) => {
    const ch = chapters[idx];
    const prev = idx > 0 ? chapters[idx - 1] : null;
    return ch?.part !== null && (prev === null || prev?.part !== ch?.part);
  };

  return (
    <div
      className="min-h-screen transition-colors duration-200"
      style={{ backgroundColor: bgColor, color: textColor, "--reader-bg": bgColor } as React.CSSProperties}
    >
      {/* Book progress — top */}
      <ProgressBar percent={overallProgress} accentColor={accentColor} />

      <ReaderHeader
        bookTitle={bookTitle}
        chapterLabel={chapterLabel}
        visible={headerVisible}
        onTogglePicker={() => setShowPicker(!showPicker)}
        bookId={bookId}
        darkMode={darkMode}
        onToggleDarkMode={() => setDarkMode(!darkMode)}
        fontSize={fontSize}
        onChangeFontSize={setFontSize}
        scrollMode={scrollMode}
        onToggleScrollMode={handleToggleScrollMode}
      />

      <ChapterPicker
        chapters={chapters}
        currentChapter={currentIndex}
        accentColor={accentColor}
        open={showPicker}
        onClose={() => setShowPicker(false)}
        onSelectChapter={goToChapter}
        readChapters={savedProgress ? savedProgress.currentChapter : 0}
        glossaryUrl={annotations ? `/books/${bookId}/glossary` : undefined}
      />

      {/* Thin collapsed bar — visible when header is hidden */}
      <button
        type="button"
        className={`fixed top-0 left-0 right-0 z-30 transition-all duration-300 overflow-hidden ${
          headerVisible ? "max-h-0 opacity-0 pointer-events-none" : "max-h-9 opacity-100"
        }`}
        onClick={() => setShowPicker(true)}
      >
        <div
          className={`h-9 flex items-center justify-center gap-2 px-4 backdrop-blur-xl ${
            darkMode ? "bg-[#0a0a0a]/40" : "bg-white/40"
          }`}
        >
          <span
            className={`text-[11px] truncate text-center ${
              darkMode ? "text-white/50" : "text-black/50"
            }`}
          >
            {bookTitle} &middot; {chapterLabel}
          </span>
        </div>
      </button>

      {/* Chapter progress bar — bottom, using env() for mobile browser chrome */}
      <div
        className="fixed left-0 right-0 z-50 h-[6px] bg-transparent"
        style={{ bottom: "env(safe-area-inset-bottom, 0px)" }}
      >
        <div
          className="h-full transition-[width] duration-200 ease-out"
          style={{
            width: `${Math.min(chapterProgress, 100)}%`,
            backgroundColor: darkMode ? "rgba(255,255,255,0.25)" : "rgba(0,0,0,0.2)",
          }}
        />
      </div>

      {scrollMode === "infinite" ? (
        /* Infinite scroll: render all chapters */
        <div className="pb-32">
          {chapters.map((ch, idx) => (
            <div
              key={ch.id}
              style={{ contentVisibility: "auto", containIntrinsicSize: "auto 800px" }}
            >
              <ChapterContent
                chapter={ch}
                chapterIndex={idx}
                showPartDivider={showPartDividerForChapter(idx)}
                registerRef={registerRef}
                registerScrollTarget={registerScrollTarget}
                darkMode={darkMode}
                fontSize={fontSize}
                isFirst={idx === 0}
                chapterTerms={annotations?.chapters[ch.id]}
                glossary={annotations?.glossary}
              />
            </div>
          ))}
        </div>
      ) : (
        /* Paginated: single chapter */
        <>
          {/* Chapter image with nav overlaid */}
          {chapter?.image ? (
            <div className="relative">
              <div className="pt-12">
                <ChapterImage src={chapter.image} alt={chapter.title} />
              </div>
              {/* Prev / Next overlay on image, below the header */}
              <div className="absolute inset-x-0 top-14 flex items-center justify-between px-5 sm:px-8 max-w-[720px] mx-auto">
                <button
                  onClick={() => goToChapter(currentIndex - 1)}
                  disabled={currentIndex === 0}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors max-w-[40%] backdrop-blur-md ${
                    currentIndex === 0
                      ? "opacity-20 cursor-not-allowed"
                      : "text-white/80 hover:text-white hover:bg-white/15 bg-black/30"
                  }`}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
                    <polyline points="15 18 9 12 15 6" />
                  </svg>
                  <div className="text-left min-w-0">
                    <span className="block truncate text-xs sm:text-sm">{prevChapter ? prevChapter.title : "Previous"}</span>
                  </div>
                </button>

                <span className="text-xs text-white/50 bg-black/30 backdrop-blur-md px-2.5 py-1 rounded-md">
                  {currentIndex + 1} / {totalChapters}
                </span>

                {nextChapter ? (
                  <button
                    onClick={() => goToChapter(currentIndex + 1)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors max-w-[40%] backdrop-blur-md text-white/80 hover:text-white hover:bg-white/15 bg-black/30"
                  >
                    <div className="text-right min-w-0">
                      <span className="block truncate text-xs sm:text-sm">{nextChapter.title}</span>
                    </div>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </button>
                ) : (
                  <span className="max-w-[40%]" />
                )}
              </div>
            </div>
          ) : (
            /* No image — simple top nav */
            <div className="flex items-center justify-between px-5 sm:px-8 pt-16 pb-2 max-w-[720px] mx-auto">
              <button
                onClick={() => goToChapter(currentIndex - 1)}
                disabled={currentIndex === 0}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-[40%] ${
                  currentIndex === 0
                    ? "opacity-20 cursor-not-allowed"
                    : darkMode
                    ? "text-white/60 hover:text-white hover:bg-white/10"
                    : "text-black/60 hover:text-black hover:bg-black/5"
                }`}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
                  <polyline points="15 18 9 12 15 6" />
                </svg>
                <div className="text-left min-w-0">
                  <span className="block truncate text-xs sm:text-sm">{prevChapter ? prevChapter.title : "Previous"}</span>
                </div>
              </button>

              <span className={`text-xs ${darkMode ? "text-white/30" : "text-black/30"}`}>
                {currentIndex + 1} / {totalChapters}
              </span>

              {nextChapter ? (
                <button
                  onClick={() => goToChapter(currentIndex + 1)}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-[40%] ${
                    darkMode
                      ? "text-white/60 hover:text-white hover:bg-white/10"
                      : "text-black/60 hover:text-black hover:bg-black/5"
                  }`}
                >
                  <div className="text-right min-w-0">
                    <span className="block truncate text-xs sm:text-sm">{nextChapter.title}</span>
                  </div>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              ) : (
                <span className="max-w-[40%]" />
              )}
            </div>
          )}

          <div className="pb-32">
            {chapter && (
              <ChapterContent
                key={chapter.id}
                chapter={chapter}
                chapterIndex={currentIndex}
                showPartDivider={showPartDividerForChapter(currentIndex)}
                registerRef={() => {}}
                registerScrollTarget={() => {}}
                darkMode={darkMode}
                fontSize={fontSize}
                isFirst={false}
                hideImage
                chapterTerms={annotations?.chapters[chapter.id]}
                glossary={annotations?.glossary}
              />
            )}
          </div>

          {/* Bottom nav */}
          <div className="flex items-center justify-between px-5 sm:px-8 pb-16 max-w-[720px] mx-auto">
            <button
              onClick={() => goToChapter(currentIndex - 1)}
              disabled={currentIndex === 0}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-[40%] ${
                currentIndex === 0
                  ? "opacity-20 cursor-not-allowed"
                  : darkMode
                  ? "text-white/60 hover:text-white hover:bg-white/10"
                  : "text-black/60 hover:text-black hover:bg-black/5"
              }`}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
                <polyline points="15 18 9 12 15 6" />
              </svg>
              <div className="text-left min-w-0">
                <span className="block truncate text-xs sm:text-sm">{prevChapter ? prevChapter.title : "Previous"}</span>
                {prevChapter && (
                  <span className={`block text-[10px] mt-0.5 ${darkMode ? "text-white/30" : "text-black/30"}`}>
                    {Math.max(1, Math.round(prevChapter.wordCount / 230))} min
                  </span>
                )}
              </div>
            </button>

            <span
              className={`text-xs ${darkMode ? "text-white/30" : "text-black/30"}`}
            >
              {currentIndex + 1} / {totalChapters}
            </span>

            {currentIndex >= chapters.length - 1 ? (
              <span
                className={`text-sm italic ${darkMode ? "text-white/30" : "text-black/30"}`}
                style={{ fontFamily: "var(--font-serif)" }}
              >
                The End
              </span>
            ) : (
              <button
                onClick={() => goToChapter(currentIndex + 1)}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-[40%] ${
                  darkMode
                    ? "text-white/60 hover:text-white hover:bg-white/10"
                    : "text-black/60 hover:text-black hover:bg-black/5"
                }`}
              >
                <div className="text-right min-w-0">
                  <span className="block truncate text-xs sm:text-sm">{chapters[currentIndex + 1].title}</span>
                  <span className={`block text-[10px] mt-0.5 ${darkMode ? "text-white/30" : "text-black/30"}`}>
                    {Math.max(1, Math.round(chapters[currentIndex + 1].wordCount / 230))} min
                  </span>
                </div>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
