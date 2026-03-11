"use client";

import { Annotation, resolveGlossary } from "@/lib/types";
import AnnotatedTerm from "@/components/reader/AnnotatedTerm";

interface AnnotatedSummaryProps {
  summary: string;
  glossary: Record<string, Annotation>;
}

export default function AnnotatedSummary({ summary, glossary: rawGlossary }: AnnotatedSummaryProps) {
  const glossary = resolveGlossary(rawGlossary);
  const terms = Object.keys(glossary);
  if (terms.length === 0) {
    return <p className="text-white/60 leading-relaxed">{summary}</p>;
  }

  // Sort terms longest-first to avoid partial matches
  const sortedTerms = [...terms].sort((a, b) => b.length - a.length);
  const escaped = sortedTerms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const regex = new RegExp(`\\b(${escaped.join("|")})\\b`, "g");

  const parts = summary.split(regex);
  if (parts.length === 1) {
    return <p className="text-white/60 leading-relaxed">{summary}</p>;
  }

  return (
    <p className="text-white/60 leading-relaxed">
      {parts.map((part, i) => {
        if (!part) return null;
        const annotation = glossary[part];
        if (annotation) {
          return (
            <AnnotatedTerm key={i} term={part} annotation={annotation} darkMode={true} />
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </p>
  );
}
