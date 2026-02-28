import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "Privacy policy for Grand Old Books.",
  alternates: { canonical: "/privacy" },
};

export default function PrivacyPage() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold text-white">Privacy Policy</h1>
      <p className="text-xs text-white/30 mt-2">Last updated: February 28, 2026</p>

      <div className="mt-8 space-y-6 text-white/60 leading-relaxed">
        <section>
          <h2 className="text-lg font-semibold text-white mb-2">What We Collect</h2>
          <p>
            Grand Old Books uses Google Analytics 4 (GA4) to collect anonymous
            usage data such as pages visited, time on site, and general device
            and browser information. This helps us understand which books readers
            enjoy and improve the site.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-2">Cookies</h2>
          <p>
            Google Analytics sets cookies to distinguish unique visitors and
            track sessions. These are first-party cookies set by Google&rsquo;s
            analytics script. No advertising cookies or third-party trackers are
            used.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-2">No Personal Data</h2>
          <p>
            Grand Old Books does not require user accounts, collect email
            addresses, or store any personally identifiable information. There
            are no sign-ups, no logins, and no forms that collect personal data.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-2">Third-Party Services</h2>
          <p>
            Images and static assets may be served from Google Cloud Storage.
            Google Analytics data is processed by Google under their{" "}
            <a
              href="https://policies.google.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-white/80"
            >
              privacy policy
            </a>
            .
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-2">Contact</h2>
          <p>
            If you have questions about this privacy policy, please reach out
            via our{" "}
            <a
              href="https://docs.google.com/forms/d/e/1FAIpQLSfvPq9WvMOQfD3g89SnQiFZ814VORONau9BoXhlMhV34RbgaA/viewform"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-white/80"
            >
              feedback form
            </a>
            .
          </p>
        </section>
      </div>

      <div className="mt-12">
        <Link
          href="/"
          className="text-sm text-white/40 hover:text-white/70 transition-colors"
        >
          &larr; Back to all books
        </Link>
      </div>
    </div>
  );
}
