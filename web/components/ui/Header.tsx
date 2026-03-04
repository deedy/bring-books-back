"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Header() {
  const pathname = usePathname();
  const isSubPage = pathname !== "/";

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/40 backdrop-blur-xl border-b border-white/[0.06]">
      <nav className="max-w-4xl mx-auto px-4 h-12 flex items-center justify-between relative">
        <div className="flex items-center gap-2">
          {isSubPage && (
            <Link
              href="/"
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium tracking-wide border border-white/20 text-white/70 hover:bg-white/10 transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="15 18 9 12 15 6" />
              </svg>
              All Books
            </Link>
          )}
        </div>
        <Link href="/" className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2.5 text-lg font-semibold tracking-tight text-white pointer-events-auto" style={{ fontFamily: "var(--font-serif)" }}>
          <img src="/logo.png" alt="" className="w-7 h-7 rounded" />
          Grand Old Books
        </Link>
        <div />
      </nav>
    </header>
  );
}
