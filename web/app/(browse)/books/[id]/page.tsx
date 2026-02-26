import type { Metadata } from "next";
import Link from "next/link";
import { getCatalog, getAnnotations, getChapters } from "@/lib/data";
import ReadButton from "@/components/ReadButton";
import BookCard from "@/components/BookCard";
import BookPreview from "@/components/BookPreview";
import { readingTime } from "@/lib/utils";

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.books.map((book) => ({ id: book.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id);
  if (!book) return {};
  const author = catalog.authors.find((a) => a.id === book.authorId);
  const title = `${book.title} by ${author?.name ?? "Unknown"}`;
  const description = book.summary.slice(0, 160);
  return {
    title,
    description,
    alternates: {
      canonical: `/books/${id}`,
    },
    openGraph: {
      title,
      description,
      images: [{ url: book.coverImage }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [book.coverImage],
    },
  };
}

export default async function BookPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const catalog = getCatalog();
  const book = catalog.books.find((b) => b.id === id)!;
  const author = catalog.authors.find((a) => a.id === book.authorId)!;
  const otherBooks = catalog.books.filter(
    (b) => b.authorId === book.authorId && b.id !== book.id
  );

  const annotations = getAnnotations(id);

  // Build glossary lists sorted by frequency (most appearances first)
  type TermCard = { name: string; description: string; image?: string };
  let characters: TermCard[] = [];
  let properNouns: TermCard[] = [];
  let vocabulary: TermCard[] = [];
  let totalCharacters = 0;
  let totalProperNouns = 0;
  let totalVocabulary = 0;
  if (annotations) {
    const chaptersData = getChapters(id);
    const chapterIds = chaptersData.chapters.map((ch) => ch.id);

    // Count chapter appearances for each term
    function byFrequency(type: string): { items: TermCard[]; total: number } {
      const entries = Object.entries(annotations!.glossary).filter(
        ([, a]) => a.type === type
      );
      const withCount = entries.map(([name, a]) => {
        let count = 0;
        for (const chId of chapterIds) {
          if (annotations!.chapters[chId]?.includes(name)) count++;
        }
        return { name, description: a.description, image: a.image, count };
      });
      withCount.sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
      return { items: withCount.slice(0, 6), total: withCount.length };
    }

    const chars = byFrequency("character");
    characters = chars.items;
    totalCharacters = chars.total;
    const nouns = byFrequency("proper_noun");
    properNouns = nouns.items;
    totalProperNouns = nouns.total;
    const vocab = byFrequency("vocabulary");
    vocabulary = vocab.items;
    totalVocabulary = vocab.total;
  }

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Book",
    name: book.title,
    alternateName: book.originalTitle,
    author: { "@type": "Person", name: author.name },
    inLanguage: "en",
    genre: book.genre,
    datePublished: String(book.originalYear),
    image: `https://grandoldbooks.com${book.coverImage}`,
    url: `https://grandoldbooks.com/books/${book.id}`,
    description: book.summary,
    numberOfPages: book.totalChapters,
    publisher: { "@type": "Organization", name: "Grand Old Books" },
  };

  return (
    <div className="pb-12">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      {/* Hero Banner — fades into page background */}
      <div className="relative w-full h-[350px] -mt-4">
        <img
          src={`/data/images/heroes/${book.id}.webp`}
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        {/* Bottom fade into page bg */}
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,10,11,0) 0%, rgba(10,10,11,0.15) 40%, rgba(10,10,11,0.7) 70%, rgba(10,10,11,1) 100%)",
          }}
        />
      </div>

      {/* Book Header — overlaps banner */}
      <div className="max-w-6xl mx-auto px-6 flex flex-col md:flex-row gap-10 -mt-32 relative z-10">
        <div className="w-64 flex-shrink-0 mx-auto md:mx-0">
          <div
            className="aspect-[2/3] rounded-lg overflow-hidden"
            style={{
              boxShadow:
                "0 8px 30px rgba(0,0,0,0.5), 0 2px 8px rgba(0,0,0,0.3), 0 0 60px rgba(0,0,0,0.25)",
            }}
          >
            <img
              src={book.coverImage}
              alt={book.title}
              loading="lazy"
              className="w-full h-full object-cover"
            />
          </div>
        </div>
        <div className="flex-1 drop-shadow-[0_2px_12px_rgba(0,0,0,0.6)]">
          <h1 className="text-3xl md:text-4xl font-bold text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)]">
            {book.title}
          </h1>
          <p className="text-lg text-white/60 mt-1">{book.subtitle}</p>
          <Link
            href={`/authors/${author.id}`}
            className="text-sm text-white/50 hover:text-white/80 transition-colors mt-2 inline-block"
          >
            by {author.name}
          </Link>

          <div className="flex flex-wrap gap-2 mt-4">
            {book.genre.map((g) => (
              <span
                key={g}
                className="px-3 py-1 text-xs font-medium rounded-full bg-white/10 text-white/70"
              >
                {g}
              </span>
            ))}
          </div>

          <p className="text-sm text-white/40 mt-3 italic">
            {book.title !== book.transliteratedTitle
              ? `${book.transliteratedTitle} (${book.originalTitle})`
              : book.originalTitle}
          </p>
          <div className="flex gap-6 mt-2 text-xs text-white/40">
            <span>Originally in {book.originalLanguage}</span>
            <span>{book.originalYear}</span>
          </div>

          <div className="flex gap-6 mt-2 text-xs text-white/40">
            <span>{book.totalChapters} chapters</span>
            <span>{Math.round(book.wordCount / 1000)}k words</span>
            <span>{readingTime(book.wordCount)} read</span>
          </div>

          <div className="mt-6">
            <ReadButton bookId={book.id} accentColor={book.accentColor} />
          </div>
        </div>
      </div>

      {/* Summary */}
      <section className="max-w-6xl mx-auto px-6 mt-16">
        <h2 className="text-xl font-bold text-white mb-4">About This Book</h2>
        <p className="text-white/60 leading-relaxed max-w-3xl">
          {book.summary}
        </p>
      </section>

      {/* Characters */}
      {characters.length > 0 && (
        <section className="max-w-6xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">Characters</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-3xl">
            {characters.map((ch) => (
              <div
                key={ch.name}
                className="px-3.5 py-3 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-start gap-3"
              >
                {ch.image && (
                  <img
                    src={ch.image}
                    alt={ch.name}
                    loading="lazy"
                    className="w-14 h-14 rounded-full object-cover flex-shrink-0"
                  />
                )}
                <div className="min-w-0">
                  <p className="font-semibold text-white text-sm">{ch.name}</p>
                  <p className="text-white/50 text-xs mt-1 leading-relaxed">
                    {ch.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
          <Link
            href={`/books/${id}/glossary?type=character`}
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-4"
          >
            View all {totalCharacters} characters
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </section>
      )}

      {/* About the Author */}
      <section className="max-w-6xl mx-auto px-6 mt-16">
        <h2 className="text-xl font-bold text-white mb-4">
          About the Author
        </h2>
        <div className="flex gap-6 items-start">
          <Link href={`/authors/${author.id}`} className="flex-shrink-0">
            <div className="w-20 h-20 rounded-full overflow-hidden">
              <img
                src={author.image}
                alt={author.name}
                loading="lazy"
                className="w-full h-full object-cover"
              />
            </div>
          </Link>
          <div>
            <Link
              href={`/authors/${author.id}`}
              className="text-white font-semibold hover:text-white/80 transition-colors"
            >
              {author.name}
            </Link>
            <p className="text-xs text-white/40 mt-0.5">{author.years}</p>
            <p className="text-sm text-white/50 mt-2 leading-relaxed max-w-2xl">
              {author.bio.split("\n\n")[0]}
            </p>
          </div>
        </div>
      </section>

      {/* Preview / Continue Reading */}
      <div className="max-w-6xl mx-auto px-6">
        <BookPreview bookId={book.id} accentColor={book.accentColor} previewText={book.previewText} />
      </div>

      {/* Places and terms in this book */}
      {properNouns.length > 0 && (
        <section className="max-w-6xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-4">Places and Terms in this Book</h2>
          <div className="space-y-2 max-w-3xl">
            {properNouns.map((t) => (
              <p key={t.name} className="text-sm">
                <span className="font-medium text-white">{t.name}</span>
                <span className="text-white/40 ml-1.5">— {t.description}</span>
              </p>
            ))}
          </div>
          <Link
            href={`/books/${id}/glossary?type=proper_noun`}
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-3"
          >
            View all {totalProperNouns} places &amp; terms
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </section>
      )}

      {/* Vocabulary */}
      {vocabulary.length > 0 && (
        <section className="max-w-6xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-4">Vocabulary</h2>
          <div className="space-y-2 max-w-3xl">
            {vocabulary.map((t) => (
              <p key={t.name} className="text-sm">
                <span className="font-medium text-white">{t.name}</span>
                <span className="text-white/40 ml-1.5">— {t.description}</span>
              </p>
            ))}
          </div>
          <Link
            href={`/books/${id}/glossary?type=vocabulary`}
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-3"
          >
            View all {totalVocabulary} vocabulary
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
        </section>
      )}

      {/* Other Books */}
      {otherBooks.length > 0 && (
        <section className="max-w-6xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">
            More by {author.name}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {otherBooks.map((b) => (
              <BookCard key={b.id} book={b} author={author} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
