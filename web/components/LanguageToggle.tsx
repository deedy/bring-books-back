"use client";

import { LANGUAGE_LABELS } from "@/lib/scripts";

interface LanguageToggleProps {
  originalLanguage: string;
  originalScript: string;
  accentColor: string;
  isOriginal: boolean;
  onLanguageChange?: (lang: "english" | "original") => void;
}

export default function LanguageToggle({
  originalLanguage,
  accentColor,
  isOriginal,
  onLanguageChange,
}: LanguageToggleProps) {
  const nativeLabel = LANGUAGE_LABELS[originalLanguage] ?? originalLanguage;

  return (
    <div className="inline-flex items-center rounded-lg border border-white/15 overflow-hidden text-sm">
      <button
        onClick={() => onLanguageChange?.("english")}
        className="px-4 py-2 font-medium transition-colors"
        style={
          !isOriginal
            ? { backgroundColor: accentColor, color: "white" }
            : { color: "rgba(255,255,255,0.5)" }
        }
      >
        English
      </button>
      <button
        onClick={() => onLanguageChange?.("original")}
        className="px-4 py-2 font-medium transition-colors"
        style={
          isOriginal
            ? { backgroundColor: accentColor, color: "white" }
            : { color: "rgba(255,255,255,0.5)" }
        }
      >
        {nativeLabel}
      </button>
    </div>
  );
}
