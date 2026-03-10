"use client";

import { useEffect, useRef, useState } from "react";

interface ChapterImageProps {
  src: string;
  alt: string;
}

export default function ChapterImage({ src, alt }: ChapterImageProps) {
  const [loaded, setLoaded] = useState(false);
  const imgRef = useRef<HTMLImageElement | null>(null);

  useEffect(() => {
    setLoaded(false);
  }, [src]);

  useEffect(() => {
    const img = imgRef.current;
    if (img && img.complete && img.naturalWidth > 0) {
      setLoaded(true);
    }
  }, [src]);

  return (
    <div
      className="w-full relative overflow-hidden max-h-[50vh] md:max-h-[70vh]"
      style={{ aspectRatio: "16 / 9" }}
    >
      {/* Shimmer placeholder */}
      {!loaded && (
        <div className="absolute inset-0 bg-white/[0.04] animate-pulse" />
      )}
      <img
        ref={imgRef}
        src={src}
        alt={alt}
        loading="lazy"
        onLoad={() => setLoaded(true)}
        onError={() => setLoaded(true)}
        className={`w-full h-full object-cover object-top transition-opacity duration-500 ${
          loaded ? "opacity-100" : "opacity-0"
        }`}
      />
      {/* Gradient fade at bottom */}
      <div className="absolute inset-x-0 bottom-0 h-[40%] bg-gradient-to-t from-[var(--reader-bg)] to-transparent" />
    </div>
  );
}
