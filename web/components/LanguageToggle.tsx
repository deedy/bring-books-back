"use client";

import { LANGUAGE_LABELS } from "@/lib/scripts";

export type LanguageOption = "english" | "modern" | "original";

interface LanguageToggleProps {
  originalLanguage?: string;
  originalScript?: string;
  accentColor: string;
  active: LanguageOption;
  hasOriginal?: boolean;
  hasModern?: boolean;
  onLanguageChange?: (lang: LanguageOption) => void;
}

export default function LanguageToggle({
  originalLanguage,
  accentColor,
  active,
  hasOriginal,
  hasModern,
  onLanguageChange,
}: LanguageToggleProps) {
  const nativeLabel = originalLanguage
    ? (LANGUAGE_LABELS[originalLanguage] ?? originalLanguage)
    : null;

  const options: { key: LanguageOption; label: string }[] = [
    { key: "english", label: "English" },
  ];
  if (hasModern) options.push({ key: "modern", label: "Modern" });
  if (hasOriginal && nativeLabel) options.push({ key: "original", label: nativeLabel });

  if (options.length <= 1) return null;

  return (
    <div className="inline-flex items-center rounded-lg border border-white/15 overflow-hidden text-sm">
      {options.map((opt) => (
        <button
          key={opt.key}
          onClick={() => onLanguageChange?.(opt.key)}
          className="px-4 py-2 font-medium transition-colors"
          style={
            active === opt.key
              ? { backgroundColor: accentColor, color: "white" }
              : { color: "rgba(255,255,255,0.5)" }
          }
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
