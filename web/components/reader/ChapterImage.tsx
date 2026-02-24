"use client";

import { useState } from "react";

interface ChapterImageProps {
  src: string;
  alt: string;
}

export default function ChapterImage({ src, alt }: ChapterImageProps) {
  const [loaded, setLoaded] = useState(false);

  return (
    <div className="max-w-[720px] mx-auto px-5 sm:px-6 pt-8">
      <div className="rounded-xl overflow-hidden relative" style={{ aspectRatio: "16 / 9" }}>
        {/* Shimmer placeholder */}
        {!loaded && (
          <div className="absolute inset-0 bg-white/[0.04] animate-pulse rounded-xl" />
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
      </div>
    </div>
  );
}
