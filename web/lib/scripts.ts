/** Shared script/language configuration — single source of truth. */

export interface ScriptInfo {
  fontClass: string;
  lineHeight: number;
  googleFontFamilies: string[];
  primaryFont: string;
}

export const SCRIPT_CONFIG: Record<string, ScriptInfo> = {
  Devanagari: { fontClass: "font-devanagari", lineHeight: 1.9, googleFontFamilies: ["Tiro+Devanagari+Hindi", "Noto+Serif+Devanagari"], primaryFont: "Tiro Devanagari Hindi" },
  Bengali:    { fontClass: "font-bengali",    lineHeight: 1.9, googleFontFamilies: ["Tiro+Bangla", "Noto+Serif+Bengali"], primaryFont: "Tiro Bangla" },
  Tamil:      { fontClass: "font-tamil",      lineHeight: 1.9, googleFontFamilies: ["Tiro+Tamil", "Noto+Serif+Tamil"], primaryFont: "Tiro Tamil" },
  Malayalam:  { fontClass: "font-malayalam",  lineHeight: 1.9, googleFontFamilies: ["Noto+Serif+Malayalam"], primaryFont: "Noto Serif Malayalam" },
  Odia:       { fontClass: "font-odia",       lineHeight: 1.9, googleFontFamilies: ["Noto+Serif+Oriya"], primaryFont: "Noto Serif Oriya" },
  Telugu:     { fontClass: "font-telugu",     lineHeight: 1.9, googleFontFamilies: ["Tiro+Telugu", "Noto+Serif+Telugu"], primaryFont: "Tiro Telugu" },
  Kannada:    { fontClass: "font-kannada",    lineHeight: 1.9, googleFontFamilies: ["Tiro+Kannada", "Noto+Serif+Kannada"], primaryFont: "Tiro Kannada" },
};

export const LANGUAGE_LABELS: Record<string, string> = {
  Sanskrit: "संस्कृत",
  Hindi: "हिंदी",
  Marathi: "मराठी",
  Bengali: "বাংলা",
  Tamil: "தமிழ்",
  Malayalam: "മലയാളം",
  Odia: "ଓଡ଼ିଆ",
  Telugu: "తెలుగు",
  Kannada: "ಕನ್ನಡ",
};
