import Link from "next/link";
import type { Metadata } from "next";
import { getCatalog } from "@/lib/data";

export const metadata: Metadata = {
  title: "Page Not Found",
  robots: "noindex",
};

export default function NotFound() {
  const catalog = getCatalog();
  const topBooks = catalog.books
    .filter((b) => !b.anthologyId)
    .slice(-4)
    .reverse();

  return (
    <div className="min-h-screen bg-[#1a1a1a] flex flex-col items-center justify-center text-center px-6">
      <h1 className="text-6xl font-bold text-white/80 mb-4">404</h1>
      <p className="text-lg text-white/40 mb-10">
        This page doesn&apos;t exist.
      </p>
      <Link
        href="/"
        className="px-6 py-3 rounded-lg bg-white/10 text-white/70 hover:bg-white/15 hover:text-white transition-colors text-sm mb-16"
      >
        Back to Library
      </Link>

      <div>
        <p className="text-sm text-white/30 mb-4">Or start reading one of these</p>
        <div className="flex gap-4 justify-center">
          {topBooks.map((b) => (
            <Link key={b.id} href={`/books/${b.id}`} className="group">
              <div className="w-20 aspect-[2/3] rounded-md overflow-hidden shadow-lg transition-transform group-hover:scale-105">
                <img
                  src={b.coverImage}
                  alt={b.title}
                  className="w-full h-full object-cover"
                />
              </div>
              <p className="text-[11px] text-white/40 mt-1.5 max-w-[80px] line-clamp-2 leading-tight">
                {b.title}
              </p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
