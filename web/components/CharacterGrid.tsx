"use client";

import { useState, useEffect, useCallback } from "react";

interface Character {
  name: string;
  description: string;
  image?: string;
}

export default function CharacterGrid({ characters }: { characters: Character[] }) {
  const [selected, setSelected] = useState<Character | null>(null);

  const close = useCallback(() => setSelected(null), []);

  useEffect(() => {
    if (!selected) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [selected, close]);

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {characters.map((ch) => (
          <button
            key={ch.name}
            onClick={() => setSelected(ch)}
            className="px-3.5 py-3 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-start gap-3 text-left hover:bg-white/[0.07] transition-colors cursor-pointer"
          >
            {ch.image && (
              <img
                src={ch.image}
                alt={ch.name}
                loading="lazy"
                className="w-14 h-14 rounded-full object-cover flex-shrink-0"
              />
            )}
            <div className="min-w-0">
              <p className="font-semibold text-white text-sm">{ch.name}</p>
              <p className="text-white/50 text-xs mt-1 leading-relaxed">
                {ch.description}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* Modal */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          onClick={close}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" />

          {/* Modal content */}
          <div
            className="relative bg-[#1a1a1b] border border-white/10 rounded-xl max-w-sm w-full p-6 flex flex-col items-center text-center shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={close}
              className="absolute top-3 right-3 text-white/40 hover:text-white/80 transition-colors"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>

            {selected.image && (
              <img
                src={selected.image}
                alt={selected.name}
                className="w-40 h-40 rounded-full object-cover shadow-lg"
              />
            )}
            <h3 className="text-xl font-bold text-white mt-4">{selected.name}</h3>
            <p className="text-sm text-white/55 mt-2 leading-relaxed">
              {selected.description}
            </p>
          </div>
        </div>
      )}
    </>
  );
}
