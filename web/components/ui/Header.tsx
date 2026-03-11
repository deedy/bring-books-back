"use client";

import { UserButton, useAuth, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { usePathname } from "next/navigation";
import SiteSearch from "@/components/search/SiteSearch";
import { useHeaderBack } from "@/lib/headerContext";

const OFFLINE_ENABLED = process.env.NEXT_PUBLIC_ENABLE_OFFLINE === "true";

export default function Header() {
  const { isLoaded, userId } = useAuth();
  const { user } = useUser();
  const pathname = usePathname();
  const isSubPage = pathname !== "/";
  const backOverride = useHeaderBack();

  const backLabel = backOverride?.label ?? "All Books";
  const backHref = backOverride?.href ?? "/";

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-[#0a0a0a]/40 backdrop-blur-xl border-b border-white/[0.06]">
      <nav className="max-w-4xl mx-auto px-4 h-12 flex items-center justify-between relative">
        <div className="flex items-center gap-2">
          {isSubPage && (
            <Link
              href={backHref}
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium tracking-wide border border-white/20 text-white/70 hover:bg-white/10 transition-colors max-w-[160px]"
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
              <span className="truncate">{backLabel}</span>
            </Link>
          )}
          <SiteSearch />
        </div>
        <Link href="/" className="absolute left-1/2 -translate-x-1/2 flex items-center gap-2.5 text-lg font-semibold tracking-tight text-white pointer-events-auto" style={{ fontFamily: "var(--font-serif)" }}>
          <img src="/logo.png" alt="" className="w-7 h-7 rounded" />
          <span className={isSubPage ? "hidden sm:inline" : ""}>Grand Old Books</span>
        </Link>
        <div className="flex items-center gap-2">
          {!isLoaded ? (
            <div className="w-7 h-7" />
          ) : !userId ? (
            <Link
              href="/sign-in"
              className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium tracking-wide bg-white text-black hover:opacity-90 transition-opacity"
            >
              Sign in
            </Link>
          ) : (
            <div
              className="flex items-center gap-2 bg-white/[0.06] hover:bg-white/[0.1] rounded-full pl-1 pr-3 py-1 cursor-pointer transition-colors"
              onClick={(e) => {
                // Click the Clerk UserButton avatar if the click wasn't directly on it
                const btn = e.currentTarget.querySelector<HTMLButtonElement>("button");
                if (btn && e.target !== btn && !btn.contains(e.target as Node)) {
                  btn.click();
                }
              }}
            >
              <UserButton>
                {OFFLINE_ENABLED && (
                  <UserButton.MenuItems>
                    <UserButton.Link
                      label="Downloads"
                      labelIcon={<DownloadIcon />}
                      href="/downloads"
                    />
                  </UserButton.MenuItems>
                )}
              </UserButton>
              {user?.firstName && (
                <span className="text-xs font-medium text-white/70 select-none">
                  {user.firstName}
                </span>
              )}
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}

function DownloadIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
      <path d="M8 2v8m0 0l-3-3m3 3l3-3M3 13h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
