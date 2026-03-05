import type { Metadata } from "next";
import Link from "next/link";
import { getCatalog, getAnnotations, getChapters, getAnthologyData } from "@/lib/data";
import BookCard from "@/components/BookCard";
import ShareButtons from "@/components/ShareButtons";
import BookOpenTracker from "@/components/BookOpenTracker";
import ReadActions from "@/components/ReadActions";
import CharacterGrid from "@/components/CharacterGrid";
import ChapterList from "@/components/ChapterList";
import StoryGrid from "@/components/StoryGrid";
import AnnotatedSummary from "@/components/AnnotatedSummary";
import { readingTime, displayYear } from "@/lib/utils";

export function generateStaticParams() {
  const catalog = getCatalog();
  const isProd = process.env.NODE_ENV === "production";
  return catalog.books.filter((b) => !isProd || b.enabled !== false).map((book) => ({ id: book.id }));
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
  const ogImage = `https://storage.googleapis.com/grandoldbooks-assets${book.coverImage.replace(".webp", ".png")}`;
  return {
    title,
    description,
    alternates: {
      canonical: `/books/${id}`,
    },
    openGraph: {
      title,
      description,
      images: [{ url: ogImage }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [ogImage],
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

  const isAnthology = book.type === "anthology";

  // For anthologies: load story-books from catalog
  const anthologyData = isAnthology ? getAnthologyData(id) : null;
  const storyBooks = isAnthology && anthologyData
    ? anthologyData.storyBookIds
        .map((sid) => catalog.books.find((b) => b.id === sid))
        .filter(Boolean) as typeof catalog.books
    : [];

  // For regular books: load chapters, annotations, etc.
  // For anthologies: merge glossary from all story-books for annotated summary
  const annotations = !isAnthology ? getAnnotations(id) : null;
  const anthologyGlossary = isAnthology && anthologyData
    ? (() => {
        const merged: Record<string, import("@/lib/types").Annotation> = {};
        for (const sid of anthologyData.storyBookIds) {
          const ann = getAnnotations(sid);
          if (ann) {
            for (const [term, entry] of Object.entries(ann.glossary)) {
              if (!merged[term]) merged[term] = entry;
            }
          }
        }
        return Object.keys(merged).length > 0 ? merged : null;
      })()
    : null;
  const chaptersData = !isAnthology ? getChapters(id) : null;
  const chaptersForList = chaptersData
    ? chaptersData.chapters.map(({ paragraphs, ...rest }) => rest)
    : [];

  // For anthology member books: find siblings
  const otherBooks = isAnthology
    ? []
    : catalog.books.filter(
        (b) => b.authorId === book.authorId && b.id !== book.id && !b.anthologyId
      );

  // Build glossary lists sorted by frequency (most appearances first)
  type TermCard = { name: string; description: string; image?: string };
  let characters: TermCard[] = [];
  let properNouns: TermCard[] = [];
  let vocabulary: TermCard[] = [];
  let totalCharacters = 0;
  let totalProperNouns = 0;
  let totalVocabulary = 0;
  if (annotations && chaptersData) {
    const chapterIds = chaptersData.chapters.map((ch) => ch.id);

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
      <div className="relative w-full h-[200px] md:h-[350px] -mt-4">
        <img
          src={
            !isAnthology && chaptersData?.chapters.length === 1 && chaptersData.chapters[0].image
              ? chaptersData.chapters[0].image
              : `/data/images/heroes/${id}.webp`
          }
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(to bottom, rgba(10,10,11,0) 0%, rgba(10,10,11,0.15) 40%, rgba(10,10,11,0.7) 70%, rgba(10,10,11,1) 100%)",
          }}
        />
      </div>

      {/* Book Header — overlaps banner */}
      <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row gap-10 -mt-32 relative z-10">
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
          {/* Breadcrumb for anthology members */}
          {book.anthologyId && (
            <Link
              href={`/books/${book.anthologyId}`}
              className="text-xs text-white/40 hover:text-white/60 transition-colors mb-2 inline-block"
            >
              &larr; {catalog.books.find((b) => b.id === book.anthologyId)?.title ?? "Back to collection"}
            </Link>
          )}

          {isAnthology && (
            <div className="flex items-center gap-1.5 mb-2">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/50">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
              </svg>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-white/50 -ml-2.5">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20" />
              </svg>
              <span className="text-xs font-semibold uppercase tracking-widest text-white/50">Story Collection</span>
            </div>
          )}
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
            {isAnthology && book.totalStories && (
              <span
                className="px-3 py-1 text-xs font-semibold rounded-full text-white"
                style={{ backgroundColor: book.accentColor }}
              >
                {book.totalStories} stories
              </span>
            )}
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
            <span>{displayYear(book.originalYear, book.yearEnd)}</span>
          </div>

          <div className="flex gap-6 mt-2 text-xs text-white/40">
            {book.storyNumber && (
              <span>Story #{book.storyNumber}</span>
            )}
            {(isAnthology ? book.totalStories : book.totalChapters > 1) && (
              <span>
                {isAnthology && book.totalStories
                  ? `${book.totalStories} stories`
                  : `${book.totalChapters} chapters`}
              </span>
            )}
            <span>{Math.round(book.wordCount / 1000)}k words</span>
            <span>{readingTime(book.wordCount)} read</span>
          </div>

          {/* Read/Download only for non-anthologies */}
          {!isAnthology && (
            <>
              <ReadActions
                bookId={book.id}
                accentColor={book.accentColor}
                totalChapters={book.totalChapters}
                hasOriginalText={book.hasOriginalText}
                originalLanguage={book.originalLanguage}
                originalScript={book.originalScript}
              />
              <BookOpenTracker bookId={book.id} />
            </>
          )}

          <div className="mt-4">
            <ShareButtons url={`/books/${book.id}`} title={`${book.title} by ${author.name}`} />
          </div>
        </div>
      </div>

      {/* Summary */}
      <section className="max-w-4xl mx-auto px-6 mt-16">
        <h2 className="text-xl font-bold text-white mb-4">
          {isAnthology ? "About This Collection" : "About This Book"}
        </h2>
        {annotations ? (
          <AnnotatedSummary summary={book.summary} glossary={annotations.glossary} />
        ) : anthologyGlossary ? (
          <AnnotatedSummary summary={book.summary} glossary={anthologyGlossary} />
        ) : (
          <p className="text-white/60 leading-relaxed">{book.summary}</p>
        )}
      </section>

      {/* Anthology: Story-book grid */}
      {isAnthology && storyBooks.length > 0 && (
        <section className="max-w-5xl mx-auto px-6 mt-16">
          <StoryGrid stories={storyBooks} />
        </section>
      )}

      {/* Regular book: Chapters (hide for single-chapter books) */}
      {!isAnthology && chaptersForList.length > 1 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">Chapters</h2>
          <ChapterList chapters={chaptersForList} bookId={book.id} accentColor={book.accentColor} />
        </section>
      )}

      {/* Characters */}
      {characters.length > 0 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-6">Characters</h2>
          <CharacterGrid characters={characters} />
          {totalCharacters > 6 && (
            <Link
              href={`/books/${id}/glossary?type=character`}
              className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors mt-4"
            >
              View all {totalCharacters} characters
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </Link>
          )}
        </section>
      )}

      {/* About the Author */}
      <section className="max-w-4xl mx-auto px-6 mt-16">
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
            <p className="text-sm text-white/50 mt-2 leading-relaxed">
              {author.bio.split("\n\n")[0]}
            </p>
          </div>
        </div>
      </section>

      {/* Places and terms in this book */}
      {properNouns.length > 0 && (
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-4">Places and Terms in this Book</h2>
          <div className="space-y-2">
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
        <section className="max-w-4xl mx-auto px-6 mt-16">
          <h2 className="text-xl font-bold text-white mb-4">Vocabulary</h2>
          <div className="space-y-2">
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
        <section className="max-w-4xl mx-auto px-6 mt-16">
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
