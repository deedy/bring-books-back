import Link from "next/link";

export default function OfflineUnavailablePage() {
  return (
    <section className="max-w-3xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold text-white">This page is not available offline</h1>
      <p className="text-white/50 mt-4 leading-relaxed">
        Reconnect to the internet, or open a book that you have already saved offline.
      </p>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link
          href="/downloads"
          className="inline-flex items-center px-4 py-2 rounded-lg border border-white/10 text-white/60 hover:text-white/80 hover:bg-white/5 transition-colors"
        >
          Go to downloads
        </Link>
        <Link
          href="/"
          className="inline-flex items-center px-4 py-2 rounded-lg border border-white/10 text-white/60 hover:text-white/80 hover:bg-white/5 transition-colors"
        >
          Back home
        </Link>
      </div>
    </section>
  );
}
