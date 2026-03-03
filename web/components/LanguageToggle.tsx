"use client";

import { useState } from "react";

const languageLabels: Record<string, string> = {
  Hindi: "हिंदी",
  Marathi: "मराठी",
  Bengali: "বাংলা",
  Tamil: "தமிழ்",
  Malayalam: "മലയാളം",
  Odia: "ଓଡ଼ିଆ",
  Telugu: "తెలుగు",
  Kannada: "ಕನ್ನಡ",
};

interface LanguageToggleProps {
  originalLanguage: string;
  originalScript: string;
  accentColor: string;
  onLanguageChange?: (lang: "english" | "original") => void;
}

export default function LanguageToggle({
  originalLanguage,
  accentColor,
  onLanguageChange,
}: LanguageToggleProps) {
  const [isOriginal, setIsOriginal] = useState(false);
  const nativeLabel = languageLabels[originalLanguage] ?? originalLanguage;

  return (
    <div className="inline-flex items-center rounded-lg border border-white/15 overflow-hidden text-sm">
      <button
        onClick={() => { setIsOriginal(false); onLanguageChange?.("english"); }}
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
        onClick={() => { setIsOriginal(true); onLanguageChange?.("original"); }}
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
