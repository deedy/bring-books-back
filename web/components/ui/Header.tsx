"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();
  const isBookPage = pathname.startsWith("/books/") && pathname.split("/").length === 3;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/40 backdrop-blur-xl border-b border-white/[0.06]">
      <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-4">
          {isBookPage && (
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-sm font-medium tracking-wide border border-white/15 text-white/60 hover:text-white/90 hover:border-white/30 hover:bg-white/5 transition-all"
            >
              <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
                <path d="M10 12L6 8l4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              All Books
            </Link>
          )}
          <Link href="/" className="flex items-center gap-2.5 text-lg font-semibold tracking-tight text-white">
            <img src="/logo.png" alt="" className="w-7 h-7 rounded" />
            Grand Old Books
          </Link>
        </div>
      </nav>
    </header>
  );
}
