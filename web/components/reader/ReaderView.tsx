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
import { trackEvent } from "@/lib/analytics";
import { decodeQuoteHash } from "@/lib/quote";
import type { QuoteHighlight } from "./ChapterContent";
import SelectionSharePopover from "./SelectionSharePopover";

interface ReaderViewProps {
  bookId: string;
  bookTitle: string;
  authorName: string;
  accentColor: string;
  coverImage: string;
  originalYear: number;
  chapters: Chapter[];
  totalChapters: number;
  initialChapter?: number;
  annotations?: AnnotationsData;
}

export default function ReaderView({
  bookId,
  bookTitle,
  authorName,
  accentColor,
  coverImage,
  originalYear,
  chapters,
  totalChapters,
  initialChapter,
  annotations,
}: ReaderViewProps) {
  const updateProgress = useReadingStore((s) => s.updateProgress);
  const scrollMode = useReadingStore((s) => s.scrollMode);
  const setScrollMode = useReadingStore((s) => s.setScrollMode);

  const [currentIndex, setCurrentIndex] = useState(() => {
    if (initialChapter !== undefined && initialChapter >= 1 && initialChapter <= chapters.length) {
      return initialChapter - 1;
    }
    return useReadingStore.getState().progress[bookId]?.currentChapter ?? 0;
  });
  const [showPicker, setShowPicker] = useState(false);
  const [headerVisible, setHeaderVisible] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [fontSize, setFontSize] = useState<"small" | "medium" | "large">("medium");
  const [chapterProgress, setChapterProgress] = useState(0);
  const lastScrollY = useRef(0);
  const hasRestoredRef = useRef(false);
  const latestScrollPercentRef = useRef(0);
  // Capture the initial hash synchronously during render (before effects run),
  // because the URL-sync effect will strip the hash via replaceState.
  const initialHashRef = useRef(
    typeof window !== "undefined" ? window.location.hash : ""
  );
  // When arriving via a quote deep-link (#q=...), suppress all reading-progress writes
  // so the visitor's saved position isn't overwritten.
  const isQuoteLinkRef = useRef(
    !!decodeQuoteHash(initialHashRef.current)
  );

  // Ref for the chapter text container (used by SelectionSharePopover)
  const contentContainerRef = useRef<HTMLDivElement>(null);

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
          window.history.pushState({}, "", chapterUrl(idx));
          setTimeout(() => { suppressObserverRef.current = false; }, 200);
        }
      } else {
        setCurrentIndex(idx);
        window.scrollTo({ top: 0, behavior: "auto" });
        window.history.pushState({}, "", chapterUrl(idx));
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

  // Sync URL on every chapter change; only write to store when chapter actually changes
  useEffect(() => {
    // Preserve quote hash in URL so the highlight link remains shareable
    const hash = isQuoteLinkRef.current ? initialHashRef.current : "";
    window.history.replaceState({}, "", chapterUrl(currentIndex) + hash);
    if (isQuoteLinkRef.current) return; // Don't overwrite saved position on quote links
    // Check stored chapter — skip write on initial mount to avoid corrupting
    // scrollPercent before Zustand persist has hydrated from localStorage
    const stored = useReadingStore.getState().progress[bookId];
    if (!stored || stored.currentChapter === currentIndex) return;
    // User changed chapters — save new chapter and reset scroll to top
    updateProgress(bookId, { currentChapter: currentIndex, scrollPercent: 0 });
    latestScrollPercentRef.current = 0;
  }, [bookId, currentIndex, updateProgress, chapterUrl]);

  // Track chapter start for analytics
  useEffect(() => {
    if (chapter) {
      trackEvent("chapter_start", {
        book_id: bookId,
        chapter_id: chapter.id,
        chapter_number: chapter.number,
      });
    }
  }, [bookId, chapter?.id, chapter?.number, chapter]);

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

  // Scroll tracking: header visibility + chapter progress + save position
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
            const pct = Math.max(0, Math.min(100, ((y - chapterTop) / chapterHeight) * 100));
            latestScrollPercentRef.current = pct;
            // UI progress bar uses a visual offset
            setChapterProgress(Math.max(0, Math.min(100, ((y - chapterTop + window.innerHeight * 0.3) / chapterHeight) * 100)));
          }
        }
      } else {
        // Paginated: whole-page progress = within-chapter progress
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (scrollHeight > 0) {
          const pct = Math.min(100, (y / scrollHeight) * 100);
          latestScrollPercentRef.current = pct;
          setChapterProgress(pct);
        }
      }

    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, [scrollMode, currentIndex]);

  // One-time restore of exact scroll position on initial mount
  // Skip if a quote deep-link hash is present — the quote highlight effect handles scrolling instead.
  useEffect(() => {
    if (hasRestoredRef.current) return;

    // Delay: 300ms lets Zustand hydrate + content render + infinite chapter-scroll (50ms) settle
    const timer = setTimeout(() => {
      if (hasRestoredRef.current) return;
      hasRestoredRef.current = true;

      // If there's a quote hash, skip scroll restore — let the quote highlight effect handle it
      if (isQuoteLinkRef.current) return;

      // Read directly from store (not render closure) to guarantee hydrated state
      const state = useReadingStore.getState();
      const progress = state.progress[bookId];
      const pct = progress?.scrollPercent;
      if (!pct || pct <= 0) return;

      // Only restore if displayed chapter matches saved chapter
      if (progress.currentChapter !== currentIndex) return;

      if (state.scrollMode === "infinite") {
        // Infinite: scroll to within-chapter offset
        const headingEl = chapterHeadingRefs.current.get(currentIndex);
        const nextHeadingEl = chapterHeadingRefs.current.get(currentIndex + 1);
        if (headingEl) {
          const chapterTop = headingEl.getBoundingClientRect().top + window.scrollY;
          const chapterBottom = nextHeadingEl
            ? nextHeadingEl.getBoundingClientRect().top + window.scrollY
            : document.documentElement.scrollHeight;
          const chapterHeight = chapterBottom - chapterTop;
          if (chapterHeight > 0) {
            suppressObserverRef.current = true;
            window.scrollTo({ top: chapterTop + (pct / 100) * chapterHeight - 60, behavior: "auto" });
            setTimeout(() => { suppressObserverRef.current = false; }, 200);
          }
        }
      } else {
        // Paginated: within-chapter percent = whole-page percent
        const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
        if (scrollHeight > 0) {
          window.scrollTo({ top: (pct / 100) * scrollHeight, behavior: "auto" });
        }
      }
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bookId]);

  // Flush scroll position to store on page hide, beforeunload, and component unmount
  // (beforeunload covers tab close; visibilitychange covers mobile tab switch;
  //  cleanup covers Next.js client-side navigation where beforeunload doesn't fire)
  useEffect(() => {
    const savePosition = () => {
      if (isQuoteLinkRef.current) return; // Don't overwrite saved position on quote links
      updateProgress(bookId, { scrollPercent: latestScrollPercentRef.current });
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") savePosition();
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("beforeunload", savePosition);
    return () => {
      savePosition();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("beforeunload", savePosition);
    };
  }, [bookId, updateProgress]);

  // Handle browser back/forward: map URL back to chapter index
  useEffect(() => {
    const handlePopState = () => {
      const path = window.location.pathname;
      for (let i = 0; i < chapters.length; i++) {
        if (path === chapterUrl(i)) {
          suppressObserverRef.current = true;
          setCurrentIndex(i);
          if (scrollMode === "infinite") {
            const target = chapterScrollTargetRefs.current.get(i) ?? chapterHeadingRefs.current.get(i);
            if (target) {
              target.scrollIntoView({ behavior: "auto", block: "start" });
              window.scrollBy(0, -60);
            }
          } else {
            window.scrollTo({ top: 0, behavior: "auto" });
          }
          setTimeout(() => { suppressObserverRef.current = false; }, 200);
          return;
        }
      }
      // URL doesn't match any chapter — let the browser handle it (e.g. back to book page)
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [chapters, chapterUrl, scrollMode]);

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

  // Deep-link quote highlight: React-managed state instead of imperative DOM.
  // Parse the hash captured at render time and set highlight state.
  const [quoteHighlight, setQuoteHighlight] = useState<QuoteHighlight | null>(() => {
    const pos = decodeQuoteHash(initialHashRef.current);
    if (!pos) return null;
    return { paragraphIndex: pos.paragraphIndex, accentColor };
  });

  // Listen for hashchange so quote links work when already on the page
  useEffect(() => {
    const onHashChange = () => {
      const pos = decodeQuoteHash(window.location.hash);
      if (pos) {
        setQuoteHighlight({ paragraphIndex: pos.paragraphIndex, accentColor });
      }
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [accentColor]);

  // Scroll the highlighted paragraph into view via ref callback.
  // Uses a ref to track the last highlighted index so it scrolls again on change.
  const lastHighlightedPara = useRef<number | null>(null);
  const onHighlightRef = useCallback((el: HTMLElement | null) => {
    if (!el) return;
    const idx = quoteHighlight?.paragraphIndex ?? null;
    if (idx === lastHighlightedPara.current) return;
    lastHighlightedPara.current = idx;
    // Delay to let content render + layout settle
    setTimeout(() => {
      // Force contentVisibility on ancestor wrappers so paragraph is laid out
      let parent: HTMLElement | null = el.parentElement;
      while (parent) {
        if (parent.style.contentVisibility === "auto") {
          parent.style.contentVisibility = "visible";
        }
        parent = parent.parentElement;
      }
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  }, [quoteHighlight]);

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

  // Unique ID for scoping ::selection styles to this reader instance
  const selectionStyleId = "reader-selection";

  return (
    <div
      ref={contentContainerRef}
      id={selectionStyleId}
      className="min-h-screen transition-colors duration-200"
      style={{ backgroundColor: bgColor, color: textColor, "--reader-bg": bgColor } as React.CSSProperties}
    >
      {/* Text selection color using book's accent */}
      <style>{`#${selectionStyleId} ::selection { background-color: ${accentColor}40; color: inherit; }`}</style>

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
        readChapters={currentIndex}
        glossaryUrl={annotations ? `/books/${bookId}/glossary` : undefined}
      />

      {/* Thin collapsed bar — visible when header is hidden */}
      <button
        type="button"
        className={`fixed top-0 left-0 right-0 z-30 transition-all duration-300 overflow-hidden ${
          headerVisible ? "max-h-0 opacity-0 pointer-events-none" : "max-h-16 opacity-100"
        }`}
        onClick={() => setShowPicker(true)}
      >
        <div
          className={`h-9 flex items-center justify-center gap-2 px-4 backdrop-blur-xl ${
            darkMode ? "bg-[#0a0a0a]/40" : "bg-white/40"
          }`}
          style={{ marginTop: "env(safe-area-inset-top, 0px)" }}
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

      {/* Chapter progress bar — bottom */}
      <div
        className="fixed bottom-0 left-0 right-0 z-50 h-[6px] bg-transparent"
      >
        <div
          className="h-full transition-[width] duration-200 ease-out"
          style={{
            width: `${Math.min(chapterProgress, 100)}%`,
            backgroundColor: darkMode ? "rgba(255,255,255,0.25)" : "rgba(0,0,0,0.2)",
          }}
        />
      </div>

      <SelectionSharePopover
        accentColor={accentColor}
        bookTitle={bookTitle}
        authorName={authorName}
        coverImage={coverImage}
        originalYear={originalYear}
        chapterTitle={chapter?.title ?? ""}
        containerRef={contentContainerRef}
      />

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
                quoteHighlight={quoteHighlight ?? undefined}
                onHighlightRef={onHighlightRef}
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
              <div className="absolute inset-x-0 top-14 grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-5 sm:px-8 max-w-[720px] mx-auto">
                <div className="min-w-0">
                  <button
                    onClick={() => goToChapter(currentIndex - 1)}
                    disabled={currentIndex === 0}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors max-w-full backdrop-blur-md ${
                      currentIndex === 0
                        ? "opacity-20 cursor-not-allowed"
                        : "text-white/80 hover:text-white hover:bg-white/15 bg-black/30"
                    }`}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="flex-shrink-0">
                      <polyline points="15 18 9 12 15 6" />
                    </svg>
                    <span className="truncate text-xs sm:text-sm">{prevChapter ? prevChapter.title : "Previous"}</span>
                  </button>
                </div>

                <span className="text-xs text-white/50 bg-black/30 backdrop-blur-md px-2.5 py-1 rounded-md whitespace-nowrap">
                  {currentIndex + 1} / {totalChapters}
                </span>

                <div className="min-w-0 flex justify-end">
                  {nextChapter ? (
                    <button
                      onClick={() => goToChapter(currentIndex + 1)}
                      className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors max-w-full backdrop-blur-md text-white/80 hover:text-white hover:bg-white/15 bg-black/30"
                    >
                      <span className="truncate text-xs sm:text-sm">{nextChapter.title}</span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="9 18 15 12 9 6" />
                      </svg>
                    </button>
                  ) : (
                    <span />
                  )}
                </div>
              </div>
            </div>
          ) : (
            /* No image — simple top nav */
            <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-5 sm:px-8 pt-16 pb-2 max-w-[720px] mx-auto">
              <div className="min-w-0">
                <button
                  onClick={() => goToChapter(currentIndex - 1)}
                  disabled={currentIndex === 0}
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-full ${
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
                  <span className="truncate text-xs sm:text-sm">{prevChapter ? prevChapter.title : "Previous"}</span>
                </button>
              </div>

              <span className={`text-xs whitespace-nowrap ${darkMode ? "text-white/30" : "text-black/30"}`}>
                {currentIndex + 1} / {totalChapters}
              </span>

              <div className="min-w-0 flex justify-end">
                {nextChapter ? (
                  <button
                    onClick={() => goToChapter(currentIndex + 1)}
                    className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-full ${
                      darkMode
                        ? "text-white/60 hover:text-white hover:bg-white/10"
                        : "text-black/60 hover:text-black hover:bg-black/5"
                    }`}
                  >
                    <span className="truncate text-xs sm:text-sm">{nextChapter.title}</span>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="9 18 15 12 9 6" />
                    </svg>
                  </button>
                ) : (
                  <span />
                )}
              </div>
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
                quoteHighlight={quoteHighlight ?? undefined}
                onHighlightRef={onHighlightRef}
              />
            )}
          </div>

          {/* Bottom nav */}
          <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 px-5 sm:px-8 pb-16 max-w-[720px] mx-auto">
            <div className="min-w-0">
              <button
                onClick={() => goToChapter(currentIndex - 1)}
                disabled={currentIndex === 0}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-full ${
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
            </div>

            <span
              className={`text-xs whitespace-nowrap ${darkMode ? "text-white/30" : "text-black/30"}`}
            >
              {currentIndex + 1} / {totalChapters}
            </span>

            <div className="min-w-0 flex justify-end">
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
                  className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-colors max-w-full ${
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
          </div>
        </>
      )}
    </div>
  );
}
