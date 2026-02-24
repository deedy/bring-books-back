"use client";

import { useEffect, useRef } from "react";
import { Chapter } from "@/lib/types";

interface ChapterPickerProps {
  chapters: Chapter[];
  currentChapter: number;
  accentColor: string;
  open: boolean;
  onClose: () => void;
  onSelectChapter: (num: number) => void;
  readChapters: number;
  glossaryUrl?: string;
}

export default function ChapterPicker({
  chapters,
  currentChapter,
  accentColor,
  open,
  onClose,
  onSelectChapter,
  readChapters,
  glossaryUrl,
}: ChapterPickerProps) {
  const currentRef = useRef<HTMLButtonElement>(null);

  // Scroll current chapter into view when drawer opens
  useEffect(() => {
    if (open && currentRef.current) {
      // Small delay to let the drawer animation start
      setTimeout(() => {
        currentRef.current?.scrollIntoView({ block: "center", behavior: "auto" });
      }, 50);
    }
  }, [open]);

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
        className={`fixed top-0 left-0 bottom-0 z-50 w-80 max-w-[85vw] bg-[#111] transform transition-transform duration-300 ease-out flex flex-col ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b border-white/10 flex-shrink-0">
          <h3 className="text-sm font-semibold text-white/80">
            Table of Contents
          </h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded"
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

                return (
                  <button
                    key={ch.id}
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
                    <span className="text-sm truncate flex-1">{ch.title}</span>
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
