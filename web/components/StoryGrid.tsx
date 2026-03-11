"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { Book } from "@/lib/types";
import { readingTime, readingTimeClock, displayYear, pageCount } from "@/lib/utils";
import OfflineBadge from "@/components/OfflineBadge";

type SortField = "chronology" | "length";
type SortDir = "asc" | "desc";

export default function StoryGrid({ stories }: { stories: Book[] }) {
  const [sortField, setSortField] = useState<SortField>("chronology");
  const [sortDir, setSortDir] = useState<SortDir>("asc");

  const sorted = useMemo(() => {
    const arr = [...stories];
    arr.sort((a, b) => {
      const val =
        sortField === "chronology"
          ? (a.storyNumber ?? 0) - (b.storyNumber ?? 0)
          : a.wordCount - b.wordCount;
      return sortDir === "asc" ? val : -val;
    });
    return arr;
  }, [stories, sortField, sortDir]);

  const toggle = (field: SortField) => {
    if (sortField === field) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortDir(field === "length" ? "desc" : "asc");
    }
  };

  const arrow = (field: SortField) => {
    if (sortField !== field) return "";
    return sortDir === "asc" ? " \u2191" : " \u2193";
  };

  return (
    <>
      <div className="flex items-center gap-2 mb-6">
        <h2 className="text-xl font-bold text-white mr-auto">Stories</h2>
        <button
          onClick={() => toggle("chronology")}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors ${
            sortField === "chronology"
              ? "bg-white/15 text-white/80"
              : "bg-white/5 text-white/40 hover:bg-white/10"
          }`}
        >
          Year{arrow("chronology")}
        </button>
        <button
          onClick={() => toggle("length")}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-full transition-colors ${
            sortField === "length"
              ? "bg-white/15 text-white/80"
              : "bg-white/5 text-white/40 hover:bg-white/10"
          }`}
        >
          Length{arrow("length")}
        </button>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-6">
        {sorted.map((sb, i) => (
          <Link key={sb.id} href={`/books/${sb.id}`} className="group block">
            <div className="relative aspect-[2/3] rounded-lg overflow-hidden shadow-lg transition-all duration-200 group-hover:scale-[1.03] group-hover:shadow-2xl bg-white/[0.06]">
              <img
                src={sb.coverImage}
                alt={sb.title}
                loading="lazy"
                className="w-full h-full object-cover"
              />
              <span className="absolute top-2 left-2 px-1.5 py-0.5 text-[10px] font-semibold rounded bg-black/60 text-white/70 backdrop-blur-sm">
                #{sb.storyNumber ?? i + 1}
              </span>
              <OfflineBadge bookId={sb.id} />
              <span className="absolute bottom-2 right-2 px-1.5 py-0.5 text-[10px] font-medium rounded bg-black/70 text-white/80 backdrop-blur-sm opacity-0 group-hover:opacity-100 transition-opacity">
                {readingTimeClock(sb.wordCount)}
              </span>
            </div>
            <div className="mt-3">
              <h3 className="text-sm font-semibold text-white line-clamp-2 leading-snug">
                {sb.title}
              </h3>
              {sb.transliteratedTitle && sb.transliteratedTitle !== sb.title && (
                <p className="text-[11px] text-white/30 mt-0.5 italic">{sb.transliteratedTitle}</p>
              )}
              <p className="text-[11px] text-white/30 mt-0.5">
                {displayYear(sb.originalYear, sb.yearEnd)} &middot;{" "}
                {sb.totalChapters === 1 ? "Short Story" : `${sb.totalChapters} chapters`} &middot;{" "}
                {pageCount(sb.wordCount)} pp &middot; {readingTime(sb.wordCount)}
              </p>
            </div>
          </Link>
        ))}
      </div>
    </>
  );
}
