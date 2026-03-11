"use client";

import { useState, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { normalizeForSearch } from "@/lib/search";
import type { GlossaryTerm } from "@/app/(browse)/books/[id]/glossary/page";

interface GlossaryContentProps {
  terms: GlossaryTerm[];
}

type TypeFilter = "all" | "character" | "proper_noun" | "vocabulary";
type SortMode = "chronological" | "frequency";

const TYPE_LABELS: { value: TypeFilter; label: string }[] = [
  { value: "all", label: "All" },
  { value: "character", label: "Characters" },
  { value: "proper_noun", label: "Places & Terms" },
  { value: "vocabulary", label: "Vocabulary" },
];

const VALID_FILTERS = new Set<string>(["all", "character", "proper_noun", "vocabulary"]);

export default function GlossaryContent({ terms }: GlossaryContentProps) {
  const searchParams = useSearchParams();
  const typeParam = searchParams.get("type") ?? "";
  const queryParam = searchParams.get("q") ?? "";
  const initialFilter: TypeFilter = VALID_FILTERS.has(typeParam)
    ? (typeParam as TypeFilter)
    : "all";

  const [filter, setFilter] = useState<TypeFilter>(initialFilter);
  const [sort, setSort] = useState<SortMode>("frequency");
  const [query, setQuery] = useState(queryParam);

  const counts = useMemo(() => {
    const c = { all: terms.length, character: 0, proper_noun: 0, vocabulary: 0 };
    for (const t of terms) c[t.type]++;
    return c;
  }, [terms]);

  const filtered = useMemo(() => {
    const list = filter === "all" ? terms : terms.filter((t) => t.type === filter);
    const normalizedQuery = normalizeForSearch(query);
    const searched = normalizedQuery
      ? list.filter((term) =>
          normalizeForSearch(`${term.name} ${term.description}`).includes(normalizedQuery)
        )
      : list;

    return [...searched].sort((a, b) =>
      sort === "chronological"
        ? a.firstChapterIndex - b.firstChapterIndex || a.name.localeCompare(b.name)
        : b.appearanceCount - a.appearanceCount || a.name.localeCompare(b.name)
    );
  }, [terms, filter, query, sort]);

  return (
    <div>
      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3 mb-8">
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search glossary terms"
          className="min-w-[220px] flex-1 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white outline-none placeholder:text-white/30 focus:border-white/20"
        />

        {/* Type filters */}
        <div className="flex gap-1 p-1 bg-white/[0.06] rounded-lg">
          {TYPE_LABELS.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setFilter(value)}
              className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
                filter === value
                  ? "bg-white/15 text-white"
                  : "text-white/40 hover:text-white/60"
              }`}
            >
              {label}
              <span className="ml-1.5 text-[10px] opacity-50">{counts[value]}</span>
            </button>
          ))}
        </div>

        {/* Sort toggle */}
        <div className="flex gap-1 p-1 bg-white/[0.06] rounded-lg">
          <button
            onClick={() => setSort("frequency")}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
              sort === "frequency"
                ? "bg-white/15 text-white"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            Most Frequent
          </button>
          <button
            onClick={() => setSort("chronological")}
            className={`px-3 py-1.5 text-xs rounded-md transition-colors ${
              sort === "chronological"
                ? "bg-white/15 text-white"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            Chronological
          </button>
        </div>
      </div>

      {/* Term list */}
      <div className="space-y-3">
        {filtered.length === 0 && (
          <p className="text-sm text-white/40">No glossary entries match this search.</p>
        )}
        {filtered.map((t) => (
          <div key={t.name} className={`py-2 ${t.image && t.type === "character" ? "flex items-start gap-4" : ""}`}>
            {t.image && t.type === "character" && (
              <img
                src={t.image}
                alt={t.name}
                loading="lazy"
                className="w-16 h-16 rounded-full object-cover flex-shrink-0 mt-0.5"
              />
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-white text-sm">{t.name}</span>
                {filter === "all" && (
                  <span className="text-[10px] text-white/25">
                    {t.type === "character" ? "character" : t.type === "proper_noun" ? "place/term" : "vocab"}
                  </span>
                )}
              </div>
              <p className="text-white/50 text-sm mt-0.5 leading-relaxed">{t.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
