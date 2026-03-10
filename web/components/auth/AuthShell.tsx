import type { ReactNode } from "react";
import Link from "next/link";
import { getCatalog } from "@/lib/data";
import { extractBookIdFromRedirect } from "@/lib/auth";
import CoverMarquee from "./CoverMarquee";

type AuthMode = "sign-in" | "sign-up";

interface AuthShellProps {
  mode: AuthMode;
  redirectUrl: string;
  children: ReactNode;
}

export default function AuthShell({
  mode,
  redirectUrl,
  children,
}: AuthShellProps) {
  const catalog = getCatalog();

  const readerBookId = extractBookIdFromRedirect(redirectUrl);
  const readerBook = readerBookId
    ? catalog.books.find((book) => book.id === readerBookId) ?? null
    : null;
  const isReaderReturn = redirectUrl.startsWith("/read/");

  // Stats for social proof
  const topLevelBooks = catalog.books.filter((b) => !b.anthologyId);
  const languageCount = new Set(topLevelBooks.map((b) => b.originalLanguage)).size;
  const totalBookCount = catalog.books.length;

  // Pick 6 diverse covers for the collage
  const coverBooks = topLevelBooks.slice(0, 8);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/40 backdrop-blur-xl border-b border-white/[0.06]">
        <nav className="max-w-5xl mx-auto px-4 h-12 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium tracking-wide border border-white/20 text-white/70 hover:bg-white/10 transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 16 16" fill="none" className="shrink-0">
              <path
                d="M10 12L6 8l4-4"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            All Books
          </Link>
          <Link href="/" className="flex items-center gap-2.5 text-lg font-semibold tracking-tight text-white" style={{ fontFamily: "var(--font-serif)" }}>
            <img src="/logo.png" alt="" className="w-7 h-7 rounded" />
            <span className="hidden sm:inline">Grand Old Books</span>
          </Link>
          <div className="w-[88px]" /> {/* Spacer to balance layout */}
        </nav>
      </header>

      {/* Content — two-column on desktop */}
      <div className="md:min-h-screen flex items-start md:items-center justify-center pt-14 px-4">
        <div className="w-full max-w-[52rem] flex flex-col md:flex-row gap-6 md:gap-16 py-6 md:py-20">

          {/* Left column: Value proposition */}
          <div className="flex-1 flex flex-col justify-center max-w-md">
            {/* Book context banner (if coming from reader) */}
            {isReaderReturn && readerBook ? (
              <div className="mb-4 md:mb-8 flex items-center gap-4">
                <img
                  src={readerBook.coverImage}
                  alt={readerBook.title}
                  className="w-14 h-[84px] rounded-md object-cover flex-shrink-0 shadow-lg shadow-black/40"
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white/80 truncate">
                    Continue reading
                  </p>
                  <p className="text-lg font-semibold text-white mt-0.5 truncate" style={{ fontFamily: "var(--font-serif)" }}>
                    {readerBook.title}
                  </p>
                  <p className="text-xs text-white/40 mt-1">
                    Your place is saved
                  </p>
                </div>
              </div>
            ) : (
              /* Scrolling cover marquee when not returning from reader */
              <div className="mb-4 md:mb-8 -mx-4 md:mx-0">
                <CoverMarquee books={coverBooks.map((b) => ({ cover: b.coverImage, title: b.title }))} />
              </div>
            )}

            {/* Logo */}
            <Link href="/" className="inline-flex items-center gap-2.5 mb-3 md:mb-5">
              <img src="/logo.png" alt="" className="w-8 h-8 rounded" />
              <span className="text-base font-semibold tracking-tight text-white/80" style={{ fontFamily: "var(--font-serif)" }}>
                Grand Old Books
              </span>
            </Link>

            <h1
              className="text-2xl sm:text-3xl font-bold tracking-tight text-white"
              style={{ fontFamily: "var(--font-serif)" }}
            >
              {isReaderReturn
                ? `${mode === "sign-up" ? "Create a free account" : "Welcome back"}`
                : "The greatest books you have never read."}
            </h1>

            <p className="mt-2 md:mt-3 text-sm leading-relaxed text-white/50">
              {isReaderReturn
                ? "Pick up exactly where you left off. Free forever, no credit card."
                : "Free access to stories across all cultures and languages. Impeccably translated, illustrated and annotated."}
            </p>

            {/* Value props — hidden on mobile to keep form above fold */}
            <div className="mt-6 space-y-3 hidden md:block">
              {[
                { icon: "M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z", label: "A simple, fast, modern reading experience" },
                { icon: "M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253", label: `${totalBookCount} books from ${languageCount} languages` },
                { icon: "M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z", label: "Save progress, bookmarks sync across devices" },
                { icon: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z", label: "No password needed — just a magic email link" },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3">
                  <svg className="w-4 h-4 text-[#e2c48a] mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
                  </svg>
                  <span className="text-sm text-white/60">{item.label}</span>
                </div>
              ))}
            </div>

            {/* Social proof stat line */}
            <p className="mt-4 md:mt-8 text-xs text-white/30">
              Completely free. No ads. No credit card. Just great books.
            </p>
          </div>

          {/* Right column: Auth form */}
          <div className="w-full md:w-[26rem] flex-shrink-0">
            {/* Clerk form */}
            {children}

            {/* Footer */}
            <p className="mt-6 text-[11px] leading-5 text-white/30 text-center">
              We only use your email for account access.{" "}
              <Link
                href="/privacy"
                className="text-white/45 hover:text-white/60 transition-colors"
              >
                Privacy policy
              </Link>
            </p>
          </div>

        </div>
      </div>
    </div>
  );
}
