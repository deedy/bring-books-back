"use client";

import { LANGUAGE_LABELS } from "@/lib/scripts";

export type LanguageOption = "english" | "modern" | "child" | "original";

interface LanguageToggleProps {
  originalLanguage?: string;
  originalScript?: string;
  accentColor: string;
  active: LanguageOption;
  hasOriginal?: boolean;
  hasModern?: boolean;
  hasKid?: boolean;
  englishLabel?: string;
  modernLabel?: string;
  onLanguageChange?: (lang: LanguageOption) => void;
}

export default function LanguageToggle({
  originalLanguage,
  accentColor,
  active,
  hasOriginal,
  hasModern,
  hasKid,
  englishLabel,
  modernLabel,
  onLanguageChange,
}: LanguageToggleProps) {
  const nativeLabel = originalLanguage
    ? (LANGUAGE_LABELS[originalLanguage] ?? originalLanguage)
    : null;

  const options: { key: LanguageOption; label: string; sub?: string }[] = [
    { key: "english", label: englishLabel ? "English" : "English", sub: englishLabel ?? undefined },
  ];
  if (hasModern) options.push({ key: "modern", label: modernLabel ? "English" : "Modern", sub: modernLabel ?? undefined });
  if (hasKid) options.push({ key: "child", label: "Child" });
  if (hasOriginal && nativeLabel) options.push({ key: "original", label: nativeLabel });

  if (options.length <= 1) return null;

  const subtitle = active === "modern" && !modernLabel
    ? "Rewritten with AI in modern English"
    : active === "child"
      ? "Rewritten with AI for a 10-year-old audience"
      : null;

  return (
    <div>
      <div className="inline-flex items-center rounded-lg border border-white/15 overflow-hidden text-sm">
        {options.map((opt) => (
          <button
            key={opt.key}
            onClick={() => onLanguageChange?.(opt.key)}
            className="px-4 py-2 font-medium transition-colors flex flex-col items-center"
            style={
              active === opt.key
                ? { backgroundColor: accentColor, color: "white" }
                : { color: "rgba(255,255,255,0.5)" }
            }
          >
            <span>{opt.label}</span>
            {opt.sub && (
              <span className="text-[10px] opacity-60 font-normal leading-tight">{opt.sub}</span>
            )}
          </button>
        ))}
      </div>
      {subtitle && (
        <p className="text-[11px] italic text-white/30 mt-1.5">{subtitle}</p>
      )}
    </div>
  );
}
