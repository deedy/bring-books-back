"use client";

import { useEffect, useState } from "react";
import { Chapter, ResumeTarget } from "@/lib/types";
import { SCRIPT_CONFIG } from "@/lib/scripts";
import ReaderView from "./ReaderView";

interface ReaderLoaderProps {
  accentColor: string;
  annotations?: {
    glossary: Record<string, import("@/lib/types").Annotation>;
    chapters: Record<string, string[]>;
  };
  authorName: string;
  bookId: string;
  bookTitle: string;
  chapters: Chapter[];
  coverImage: string;
  initialChapter?: number;
  isAuthenticated: boolean;
  isOriginalActive: boolean;
  originalScript?: string;
  originalYear: number;
  resumeTarget: ResumeTarget | null;
  totalChapters: number;
}

export default function ReaderLoader({
  accentColor,
  annotations,
  authorName,
  bookId,
  bookTitle,
  chapters,
  coverImage,
  initialChapter,
  isAuthenticated,
  isOriginalActive,
  originalScript,
  originalYear,
  resumeTarget,
  totalChapters,
}: ReaderLoaderProps) {
  const [ready, setReady] = useState(!isOriginalActive || !originalScript || originalScript === "Latin");

  useEffect(() => {
    if (!isOriginalActive || !originalScript || originalScript === "Latin") {
      setReady(true);
      return;
    }

    let cancelled = false;

    async function loadScriptFont() {
      const script = originalScript;
      if (!script) {
        setReady(true);
        return;
      }

      const scriptInfo = SCRIPT_CONFIG[script];
      if (!scriptInfo) {
        setReady(true);
        return;
      }

      const linkId = `gfont-${script}`;
      if (!document.getElementById(linkId)) {
        const familyParam = scriptInfo.googleFontFamilies.map((family) => `family=${family}`).join("&");
        const link = document.createElement("link");
        link.id = linkId;
        link.rel = "stylesheet";
        link.href = `https://fonts.googleapis.com/css2?${familyParam}&display=swap`;
        document.head.appendChild(link);
      }

      if (!document.fonts.check(`16px "${scriptInfo.primaryFont}"`)) {
        try {
          await Promise.race([
            document.fonts.load(`16px "${scriptInfo.primaryFont}"`),
            new Promise((resolve) => setTimeout(resolve, 3000)),
          ]);
        } catch {
          // Fall back to the browser font stack if the script font fails.
        }
      }

      if (!cancelled) {
        setReady(true);
      }
    }

    setReady(false);
    loadScriptFont();

    return () => {
      cancelled = true;
    };
  }, [isOriginalActive, originalScript]);

  if (!ready) {
    return (
      <div className="fixed inset-0 bg-[#1a1a1a] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <ReaderView
      accentColor={accentColor}
      annotations={annotations}
      authorName={authorName}
      bookId={bookId}
      bookTitle={bookTitle}
      chapters={chapters}
      coverImage={coverImage}
      initialChapter={initialChapter}
      isAuthenticated={isAuthenticated}
      isOriginalActive={isOriginalActive}
      originalScript={originalScript}
      originalYear={originalYear}
      resumeTarget={resumeTarget}
      totalChapters={totalChapters}
    />
  );
}
