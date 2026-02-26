"use client";

import { useState } from "react";

interface ChapterImageProps {
  src: string;
  alt: string;
}

export default function ChapterImage({ src, alt }: ChapterImageProps) {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="w-full relative overflow-hidden" style={{ aspectRatio: "16 / 9", maxHeight: "50vh" }}>
      {/* Shimmer placeholder */}
      {!loaded && (
        <div className="absolute inset-0 bg-white/[0.04] animate-pulse" />
      )}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        className={`w-full h-full object-cover transition-opacity duration-500 ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
      />
      {/* Gradient fade at bottom — percentage-based so it scales on mobile */}
      <div className="absolute inset-x-0 bottom-0 h-[40%] bg-gradient-to-t from-[var(--reader-bg)] to-transparent" />
    </div>
  );
}
