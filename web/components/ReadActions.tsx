"use client";

import { useState, useEffect } from "react";
import ReadButton from "./ReadButton";
import DownloadButton from "./DownloadButton";
import LanguageToggle from "./LanguageToggle";
import type { LanguageOption } from "./LanguageToggle";
import { useReadingStore } from "@/lib/store";

interface ReadActionsProps {
  bookId: string;
  accentColor: string;
  totalChapters: number;
  wordCount?: number;
  hasOriginalText?: boolean;
  hasModernText?: boolean;
  hasKidText?: boolean;
  originalLanguage?: string;
  originalScript?: string;
  originalTextLanguage?: string;
}

export default function ReadActions({
  bookId,
  accentColor,
  totalChapters,
  wordCount,
  hasOriginalText,
  hasModernText,
  hasKidText,
  originalLanguage,
  originalScript,
  originalTextLanguage,
}: ReadActionsProps) {
  const setBookLanguage = useReadingStore((s) => s.setBookLanguage);
  const storedLang = useReadingStore((s) => s.bookLanguages[bookId]);
  const progress = useReadingStore((s) => s.getProgress(bookId));

  // Wait for Zustand persist hydration before rendering
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => {
    // If already hydrated (fast path), set immediately
    if (useReadingStore.persist.hasHydrated()) {
      setHydrated(true);
      return;
    }
    const unsub = useReadingStore.persist.onFinishHydration(() => setHydrated(true));
    return unsub;
  }, []);

  const showToggle = hasOriginalText || hasModernText || hasKidText;
  const languageParam = hydrated && showToggle ? storedLang : undefined;

  const handleLanguageChange = (lang: LanguageOption) => {
    if (lang === "original" && originalLanguage) {
      setBookLanguage(bookId, (originalTextLanguage ?? originalLanguage).toLowerCase());
    } else if (lang === "modern") {
      setBookLanguage(bookId, "modern");
    } else if (lang === "child") {
      setBookLanguage(bookId, "child");
    } else {
      setBookLanguage(bookId, undefined);
    }
  };

  const active: LanguageOption = !hydrated || !languageParam
    ? "english"
    : languageParam === "modern"
      ? "modern"
      : languageParam === "child"
        ? "child"
        : "original";

  // Reserve layout space but hide content until hydrated to avoid flicker
  return (
    <div style={{ visibility: hydrated ? "visible" : "hidden" }}>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <ReadButton
          bookId={bookId}
          accentColor={accentColor}
          totalChapters={totalChapters}
          languageParam={languageParam}
          progress={hydrated ? progress : null}
        />
        <DownloadButton bookId={bookId} languageParam={languageParam} wordCount={wordCount} totalChapters={totalChapters} />
      </div>
      {showToggle && (
        <div className="mt-3">
          <p className="text-xs text-white/30 mb-1.5">Read in</p>
          <LanguageToggle
            originalLanguage={originalTextLanguage ?? originalLanguage}
            originalScript={originalScript}
            accentColor={accentColor}
            active={active}
            hasOriginal={hasOriginalText}
            hasModern={hasModernText}
            hasKid={hasKidText}
            onLanguageChange={handleLanguageChange}
          />
        </div>
      )}
    </div>
  );
}
