import Link from "next/link";
import { getCatalog } from "@/lib/data";

const FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfvPq9WvMOQfD3g89SnQiFZ814VORONau9BoXhlMhV34RbgaA/viewform";
const SUPPORT_URL = "https://buymeacoffee.com/deedy";

export default function Footer() {
  const catalog = getCatalog();
  const popularBooks = catalog.books
    .filter((b) => !b.anthologyId)
    .sort((a, b) => (b.popularity ?? 0) - (a.popularity ?? 0))
    .slice(0, 6);
  const languages = [...new Set(
    catalog.books.filter((b) => !b.anthologyId).map((b) => b.originalLanguage)
  )].sort();

  return (
    <footer className="border-t border-white/10 py-12 mt-24">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Branding */}
          <div>
            <p className="text-sm font-medium text-white/60 inline-flex items-center gap-1.5">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-white/40">
                <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
              </svg>
              Grand Old Books
            </p>
            <p className="text-xs text-white/40 mt-1">
              The greatest books you've never read.
            </p>
            <a
              href={SUPPORT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400/90 hover:bg-amber-500/20 hover:text-amber-300 border border-amber-500/15 hover:border-amber-500/30 transition-all"
            >
              <span>&#128214;</span>
              Help us add more — buy us a book
            </a>
          </div>

          {/* Navigation */}
          <div>
            <p className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-3">
              Explore
            </p>
            <ul className="space-y-2">
              <li>
                <Link href="/about" className="text-sm text-white/50 hover:text-white/80 transition-colors">
                  About
                </Link>
              </li>
              <li>
                <Link href="/" className="text-sm text-white/50 hover:text-white/80 transition-colors">
                  Browse Books
                </Link>
              </li>
              <li>
                <Link href="/authors" className="text-sm text-white/50 hover:text-white/80 transition-colors">
                  Authors
                </Link>
              </li>
              <li>
                <Link href="/feed.xml" className="text-sm text-white/50 hover:text-white/80 transition-colors">
                  RSS Feed
                </Link>
              </li>
            </ul>
          </div>

          {/* Popular Books */}
          <div>
            <p className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-3">
              Popular Books
            </p>
            <ul className="space-y-2">
              {popularBooks.map((b) => (
                <li key={b.id}>
                  <Link href={`/books/${b.id}`} className="text-sm text-white/50 hover:text-white/80 transition-colors">
                    {b.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Browse by Language */}
          <div>
            <p className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-3">
              Languages
            </p>
            <ul className="space-y-2">
              {languages.map((lang) => (
                <li key={lang}>
                  <Link href={`/?lang=${encodeURIComponent(lang)}`} className="text-sm text-white/50 hover:text-white/80 transition-colors">
                    {lang}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal & Feedback */}
          <div>
            <p className="text-xs font-semibold text-white/30 uppercase tracking-wider mb-3">
              More
            </p>
            <ul className="space-y-2">
              <li>
                <Link href="/privacy" className="text-sm text-white/50 hover:text-white/80 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <a
                  href={FEEDBACK_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-white/50 hover:text-white/80 transition-colors"
                >
                  Send Feedback
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-white/5 text-center">
          <p className="text-xs text-white/30">&copy; {new Date().getFullYear()} Grand Old Books</p>
        </div>
      </div>
    </footer>
  );
}
