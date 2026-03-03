"use client";

import { useState } from "react";
import ReadButton from "./ReadButton";
import DownloadButton from "./DownloadButton";
import LanguageToggle from "./LanguageToggle";

interface ReadActionsProps {
  bookId: string;
  accentColor: string;
  totalChapters: number;
  hasOriginalText?: boolean;
  originalLanguage?: string;
  originalScript?: string;
}

export default function ReadActions({
  bookId,
  accentColor,
  totalChapters,
  hasOriginalText,
  originalLanguage,
  originalScript,
}: ReadActionsProps) {
  const [languageParam, setLanguageParam] = useState<string | undefined>(undefined);

  return (
    <>
      <div className="mt-6 flex flex-wrap items-center gap-3">
        <ReadButton
          bookId={bookId}
          accentColor={accentColor}
          totalChapters={totalChapters}
          languageParam={languageParam}
        />
        <DownloadButton bookId={bookId} />
      </div>
      {hasOriginalText && originalScript && originalLanguage && (
        <div className="mt-3">
          <p className="text-xs text-white/30 mb-1.5">Read in</p>
          <LanguageToggle
            originalLanguage={originalLanguage}
            originalScript={originalScript}
            accentColor={accentColor}
            onLanguageChange={(lang) =>
              setLanguageParam(lang === "original" ? originalLanguage.toLowerCase() : undefined)
            }
          />
        </div>
      )}
    </>
  );
}
