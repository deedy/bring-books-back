"use client";

import { useEffect, useRef, useState } from "react";
import { Chapter, SectionInfo } from "@/lib/types";

interface ChapterPickerProps {
  chapters: Chapter[];
  currentChapter: number;
  accentColor: string;
  open: boolean;
  onClose: () => void;
  onSelectChapter: (num: number) => void;
  onSelectSection?: (chapterIdx: number, sectionNumber: number, paragraphIndex: number) => void;
  readChapters: number;
  glossaryUrl?: string;
  currentSection?: number | null;
}

function SectionGrid({
  sections,
  chapterIdx,
  accentColor,
  currentSection,
  onSelect,
}: {
  sections: SectionInfo[];
  chapterIdx: number;
  accentColor: string;
  currentSection: number | null;
  onSelect: (sectionNumber: number, paragraphIndex: number) => void;
}) {
  const [jumpInput, setJumpInput] = useState("");
  const showJumpInput = sections.length >= 50;

  const handleJump = () => {
    const num = parseInt(jumpInput, 10);
    if (isNaN(num)) return;
    const sec = sections.find((s) => s.number === num);
    if (sec) {
      onSelect(sec.number, sec.paragraphIndex);
      setJumpInput("");
    }
  };

  return (
    <div className="px-3 pb-2 mb-1">
      {showJumpInput && (
        <div className="flex items-center gap-2 mb-2">
          <input
            type="number"
            min={sections[0]?.number ?? 1}
            max={sections[sections.length - 1]?.number}
            placeholder="Jump to section..."
            value={jumpInput}
            onChange={(e) => setJumpInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") handleJump(); }}
            className="flex-1 text-xs bg-white/5 border border-white/10 rounded px-2 py-1.5 text-white/70 placeholder-white/20 outline-none focus:border-white/20"
          />
          <button
            onClick={handleJump}
            className="text-xs px-2 py-1.5 rounded bg-white/10 text-white/50 hover:text-white/80 hover:bg-white/15 transition-colors"
          >
            Go
          </button>
        </div>
      )}
      <div className="grid grid-cols-8 gap-1 max-h-[200px] overflow-y-auto scrollbar-thin">
        {sections.map((sec) => {
          const isActive = currentSection === sec.number;
          return (
            <button
              key={sec.paragraphIndex}
              onClick={() => onSelect(sec.number, sec.paragraphIndex)}
              className={`text-[11px] py-1 rounded transition-colors tabular-nums ${
                isActive
                  ? "text-white font-semibold"
                  : "text-white/40 hover:text-white/70 hover:bg-white/10"
              }`}
              style={isActive ? { backgroundColor: accentColor + "40", color: accentColor } : undefined}
              title={sec.label}
            >
              {sec.number}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function ChapterPicker({
  chapters,
  currentChapter,
  accentColor,
  open,
  onClose,
  onSelectChapter,
  onSelectSection,
  readChapters,
  glossaryUrl,
  currentSection,
}: ChapterPickerProps) {
  const currentRef = useRef<HTMLButtonElement>(null);
  const [viewMode, setViewMode] = useState<"expanded" | "compact">("expanded");
  const [expandedChapter, setExpandedChapter] = useState<number | null>(null);

  // Scroll current chapter into view when drawer opens
  useEffect(() => {
    if (open && currentRef.current) {
      // Small delay to let the drawer animation start
      setTimeout(() => {
        currentRef.current?.scrollIntoView({ block: "center", behavior: "auto" });
      }, 50);
    }
  }, [open, viewMode]);

  // Close on Escape
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) {
      document.addEventListener("keydown", handleKey);
      return () => document.removeEventListener("keydown", handleKey);
    }
  }, [open, onClose]);

  // Group chapters by part, tracking original array index
  type ChapterWithIndex = Chapter & { _idx: number };
  const parts = new Map<string, ChapterWithIndex[]>();
  for (let i = 0; i < chapters.length; i++) {
    const ch = chapters[i];
    const key = ch.partName ?? "__none__";
    if (!parts.has(key)) parts.set(key, []);
    parts.get(key)!.push({ ...ch, _idx: i });
  }

  const isExpanded = viewMode === "expanded";

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-40 bg-black/60 transition-opacity duration-200 ${
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={onClose}
      />

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 bottom-0 z-50 max-w-[85vw] bg-[#111] transform transition-all duration-300 ease-out flex flex-col ${
          open ? "translate-x-0" : "translate-x-full"
        } ${isExpanded ? "w-[420px]" : "w-80"}`}
      >
        <div className="flex items-center justify-between p-4 border-b border-white/10 flex-shrink-0">
          <h3 className="text-sm font-semibold text-white/80">
            Table of Contents
          </h3>
          <div className="flex items-center gap-1">
            {/* Compact list toggle */}
            <button
              onClick={() => setViewMode("compact")}
              className="p-1.5 rounded transition-colors"
              style={
                !isExpanded
                  ? { backgroundColor: accentColor + "30", color: accentColor }
                  : undefined
              }
              aria-label="Compact view"
              title="Compact view"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className={isExpanded ? "text-white/40" : ""}
              >
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            {/* Expanded card toggle */}
            <button
              onClick={() => setViewMode("expanded")}
              className="p-1.5 rounded transition-colors"
              style={
                isExpanded
                  ? { backgroundColor: accentColor + "30", color: accentColor }
                  : undefined
              }
              aria-label="Expanded view"
              title="Expanded view"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className={!isExpanded ? "text-white/40" : ""}
              >
                <rect x="3" y="3" width="18" height="8" rx="1" />
                <rect x="3" y="13" width="18" height="8" rx="1" />
              </svg>
            </button>
            {/* Close */}
            <button
              onClick={onClose}
              className="p-1 hover:bg-white/10 rounded ml-1"
              aria-label="Close"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                className="text-white/60"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <nav className="p-2 flex-1 overflow-y-auto scrollbar-thin">
          {[...parts.entries()].map(([partName, chaps]) => (
            <div key={partName}>
              {partName !== "__none__" && (
                <div className="px-3 pt-4 pb-2">
                  <p className="text-xs tracking-wider uppercase text-white/30 font-medium">
                    {partName}
                  </p>
                </div>
              )}
              {chaps.map((ch) => {
                const isCurrent = ch._idx === currentChapter;
                const isRead = ch._idx < readChapters;
                const hasSections = !!ch.sections && ch.sections.length > 0;
                const isChapterExpanded = expandedChapter === ch._idx;

                const sectionGrid = hasSections && isChapterExpanded && (
                  <SectionGrid
                    sections={ch.sections!}
                    chapterIdx={ch._idx}
                    accentColor={accentColor}
                    currentSection={isCurrent ? currentSection ?? null : null}
                    onSelect={(secNum, paraIdx) => {
                      onSelectSection?.(ch._idx, secNum, paraIdx);
                    }}
                  />
                );

                const sectionBadge = hasSections && !isChapterExpanded && (
                  <span className="text-[10px] text-white/25 flex-shrink-0 tabular-nums">
                    {ch.sections!.length} sec
                  </span>
                );

                const toggleExpand = hasSections
                  ? (e: { stopPropagation: () => void }) => {
                      e.stopPropagation();
                      setExpandedChapter(isChapterExpanded ? null : ch._idx);
                    }
                  : undefined;

                if (isExpanded) {
                  return (
                    <div key={ch.id}>
                      <button
                        ref={isCurrent ? currentRef : undefined}
                        onClick={() => onSelectChapter(ch._idx)}
                        className={`w-full text-left p-2 rounded-lg transition-colors mb-1.5 border ${
                          isCurrent
                            ? "bg-white/[0.08] border-white/[0.15]"
                            : "bg-white/[0.03] border-white/[0.06] hover:bg-white/[0.07]"
                        }`}
                        style={isCurrent ? { borderColor: `${accentColor}66` } : undefined}
                      >
                        {/* Thumbnail */}
                        {ch.image && (
                          <div className="w-full aspect-video rounded overflow-hidden bg-white/[0.06] mb-2">
                            <img
                              src={ch.image}
                              alt=""
                              loading="lazy"
                              className="w-full h-full object-cover"
                            />
                          </div>
                        )}
                        {/* Info */}
                        <div className="px-1">
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-xs text-white/40">
                              Chapter {ch.number}
                              {isCurrent && (
                                <span
                                  className="ml-2 text-[10px] font-semibold uppercase tracking-wider"
                                  style={{ color: accentColor }}
                                >
                                  Reading
                                </span>
                              )}
                            </span>
                            <div className="flex items-center gap-1.5 flex-shrink-0">
                              {sectionBadge}
                              <span className="text-xs text-white/30">
                                {Math.max(1, Math.round(ch.wordCount / 230))}m
                              </span>
                              {isRead && (
                                <svg
                                  width="14"
                                  height="14"
                                  viewBox="0 0 24 24"
                                  fill="none"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                  className="text-white/30"
                                >
                                  <polyline points="20 6 9 17 4 12" />
                                </svg>
                              )}
                            </div>
                          </div>
                          <p className="text-sm font-semibold text-white mt-0.5">
                            {ch.title}
                          </p>
                          {ch.summary && (
                            <p className="text-xs text-white/40 mt-1 line-clamp-2 leading-relaxed">
                              {ch.summary}
                            </p>
                          )}
                          {hasSections && (
                            <span
                              role="button"
                              tabIndex={0}
                              onClick={(e) => { e.stopPropagation(); toggleExpand?.(e); }}
                              onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.stopPropagation(); toggleExpand?.(e); } }}
                              className="mt-1.5 text-[11px] text-white/30 hover:text-white/60 transition-colors flex items-center gap-1 cursor-pointer"
                            >
                              <svg
                                width="12"
                                height="12"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2"
                                className={`transition-transform ${isChapterExpanded ? "rotate-90" : ""}`}
                              >
                                <polyline points="9 18 15 12 9 6" />
                              </svg>
                              {isChapterExpanded ? "Hide" : `${ch.sections!.length} sections`}
                            </span>
                          )}
                        </div>
                      </button>
                      {sectionGrid}
                    </div>
                  );
                }

                // Compact view
                return (
                  <div key={ch.id}>
                    <button
                      ref={isCurrent ? currentRef : undefined}
                      onClick={() => onSelectChapter(ch._idx)}
                      className={`w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-3 transition-colors ${
                        isCurrent
                          ? "text-white"
                          : "text-white/50 hover:text-white/80 hover:bg-white/5"
                      }`}
                      style={
                        isCurrent
                          ? { backgroundColor: accentColor + "30" }
                          : undefined
                      }
                    >
                      <span className="text-xs w-6 text-right flex-shrink-0 opacity-50">
                        {ch.number}
                      </span>
                      <span className="text-sm flex-1 line-clamp-2">{ch.title}</span>
                      {hasSections && (
                        <button
                          onClick={toggleExpand}
                          className="text-[10px] text-white/25 hover:text-white/50 flex-shrink-0 tabular-nums flex items-center gap-0.5"
                        >
                          <svg
                            width="10"
                            height="10"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className={`transition-transform ${isChapterExpanded ? "rotate-90" : ""}`}
                          >
                            <polyline points="9 18 15 12 9 6" />
                          </svg>
                          {ch.sections!.length} sec
                        </button>
                      )}
                      <span className="text-[10px] text-white/20 flex-shrink-0 tabular-nums">
                        {Math.max(1, Math.round(ch.wordCount / 230))}m
                      </span>
                      {isRead && (
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          className="text-white/30 flex-shrink-0"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      )}
                    </button>
                    {sectionGrid}
                  </div>
                );
              })}
            </div>
          ))}
        </nav>

        {glossaryUrl && (
          <div className="flex-shrink-0 p-2 border-t border-white/[0.06]">
            <a
              href={glossaryUrl}
              className="w-full text-left px-3 py-2.5 rounded-lg flex items-center gap-3 text-white/40 hover:text-white/70 hover:bg-white/5 transition-colors"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="flex-shrink-0 ml-0.5">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              <span className="text-sm">Glossary</span>
            </a>
          </div>
        )}
      </div>
    </>
  );
}
