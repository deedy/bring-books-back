"use client";

import Link from "next/link";

export default function BrowseError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-6">
      <h1 className="text-4xl font-bold text-white/80 mb-3">Something went wrong</h1>
      <p className="text-white/40 mb-8 max-w-md">
        We had trouble loading this page. Try again or head back to the library.
      </p>
      <div className="flex gap-4">
        <button
          onClick={reset}
          className="px-5 py-2.5 rounded-lg bg-white/10 text-white/70 hover:bg-white/15 hover:text-white transition-colors text-sm"
        >
          Try again
        </button>
        <Link
          href="/"
          className="px-5 py-2.5 rounded-lg bg-white/10 text-white/70 hover:bg-white/15 hover:text-white transition-colors text-sm"
        >
          Back to Library
        </Link>
      </div>
    </div>
  );
}
