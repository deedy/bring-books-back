"use client";

export default function ReaderError({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#1a1a1a] px-6">
      <div className="text-center max-w-md">
        <h2 className="text-xl font-bold text-white mb-3">
          Something went wrong
        </h2>
        <p className="text-white/50 text-sm leading-relaxed mb-6">
          We couldn&rsquo;t load this book. The chapter data may be temporarily
          unavailable. Please try refreshing the page.
        </p>
        <button
          onClick={reset}
          className="px-5 py-2.5 rounded-lg bg-white/10 text-white text-sm font-medium hover:bg-white/20 transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
