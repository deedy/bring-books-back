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
      <div className="rounded-xl overflow-hidden">
        <img
          src={src}
          alt={alt}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          className={`w-full transition-opacity duration-500 ${
            loaded ? "opacity-100" : "opacity-0"
          }`}
        />
      </div>
    </div>
  );
}
