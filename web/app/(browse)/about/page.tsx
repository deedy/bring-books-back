import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About",
  description:
    "Grand Old Books uses AI to translate and illustrate forgotten literary classics from Indian languages into English.",
  alternates: { canonical: "/about" },
};

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-6 py-16">
      <h1 className="text-3xl font-bold text-white">About Grand Old Books</h1>

      <section className="mt-8 space-y-4 text-white/60 leading-relaxed">
        <p>
          Grand Old Books is dedicated to reviving forgotten literary
          treasures from around the world, starting with India. Many of the
          greatest novels in Hindi, Bengali, Tamil, Telugu, Odia, Marathi,
          Malayalam, and dozens of other languages have never been translated
          into English. If we don&rsquo;t do it, these may be lost to the
          annals of history. The technologies of today finally allow us to
          bring these old books back to life.
        </p>
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold text-white mb-4">How It Works</h2>
        <div className="space-y-4 text-white/60 leading-relaxed">
          <p>Every book on Grand Old Books goes through a multi-stage AI pipeline:</p>
          <ol className="list-decimal list-inside space-y-2 pl-2">
            <li>
              <span className="text-white/80 font-medium">OCR</span> &mdash;
              Scanned pages are digitized using{" "}
              <a
                href="https://www.sarvam.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-white/80"
              >
                Sarvam AI
              </a>
              &rsquo;s multilingual OCR to extract the original text.
            </li>
            <li>
              <span className="text-white/80 font-medium">Translation</span>{" "}
              &mdash; The text is translated page-by-page into English using
              GPT-4.1, preserving the author&rsquo;s voice and style.
            </li>
            <li>
              <span className="text-white/80 font-medium">Illustration</span>{" "}
              &mdash; Every chapter receives a unique AI-generated illustration
              using Google Gemini, bringing scenes to life visually.
            </li>
            <li>
              <span className="text-white/80 font-medium">Annotation</span>{" "}
              &mdash; Characters, places, and cultural terms are extracted from
              each chapter to build glossaries with descriptions and portraits.
            </li>
          </ol>
          <p>
            The result is a beautifully illustrated, freely readable English
            edition of each classic&mdash;complete with character portraits,
            place and term glossaries, and cultural context that makes these
            novels accessible to anyone, anywhere.
          </p>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold text-white mb-4">What We Ask From You</h2>
        <div className="space-y-4 text-white/60 leading-relaxed">
          <p>
            This project gets better with your help. Here&rsquo;s what we&rsquo;d
            love to hear about:
          </p>
          <ul className="list-disc list-inside space-y-1.5 pl-2">
            <li>Translation errors or awkward passages we should fix</li>
            <li>Books you&rsquo;d like to see added to the collection</li>
            <li>Languages we should expand into next</li>
            <li>Feature ideas to make this a more useful reading experience</li>
          </ul>
          <p>
            <a
              href="https://docs.google.com/forms/d/e/1FAIpQLSfvPq9WvMOQfD3g89SnQiFZ814VORONau9BoXhlMhV34RbgaA/viewform"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-white/80"
            >
              Send us feedback
            </a>
          </p>
        </div>
      </section>

      <section className="mt-12">
        <h2 className="text-xl font-bold text-white mb-4">Credits</h2>
        <div className="space-y-4 text-white/60 leading-relaxed">
          <p>
            Grand Old Books is built by{" "}
            <a
              href="https://debarghyadas.com"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-white/80"
            >
              Deedy Das
            </a>
            .
          </p>
          <p>
            All original texts featured on this site are in the public domain,
            with their copyright terms having expired in their countries of
            origin. The English translations and AI-generated illustrations are
            original works produced for this project and are provided free of
            charge for educational and cultural purposes. If you believe any
            content has been included in error, please contact us and we will
            address it promptly.
          </p>
        </div>
      </section>

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
