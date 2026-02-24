import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-[#1a1a1a] flex flex-col items-center justify-center text-center px-6">
      <h1 className="text-6xl font-bold text-white/80 mb-4">404</h1>
      <p className="text-lg text-white/40 mb-8">
        This page doesn&apos;t exist.
      </p>
      <Link
        href="/"
        className="px-6 py-3 rounded-lg bg-white/10 text-white/70 hover:bg-white/15 hover:text-white transition-colors text-sm"
      >
        Back to Library
      </Link>
    </div>
  );
}
