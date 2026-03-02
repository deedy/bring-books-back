import Link from "next/link";

const FEEDBACK_URL = "https://docs.google.com/forms/d/e/1FAIpQLSfvPq9WvMOQfD3g89SnQiFZ814VORONau9BoXhlMhV34RbgaA/viewform";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 py-12 mt-24">
      <div className="max-w-6xl mx-auto px-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {/* Branding */}
          <div>
            <p className="text-sm font-medium text-white/60">Grand Old Books</p>
            <p className="text-xs text-white/40 mt-1">
              Reviving forgotten literary treasures with AI
            </p>
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
