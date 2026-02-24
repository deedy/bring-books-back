import type { Metadata } from "next";
import Link from "next/link";
import { getCatalog } from "@/lib/data";
import ReadButton from "@/components/ReadButton";
import BookCard from "@/components/BookCard";

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

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      {/* Breadcrumb */}
      <div className="mb-8">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70 transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
          All Books
        </Link>
      </div>

      {/* Book Header */}
      <div className="flex flex-col md:flex-row gap-10">
        <div className="w-64 flex-shrink-0 mx-auto md:mx-0">
          <div className="aspect-[2/3] rounded-lg overflow-hidden shadow-2xl">
            <img
              src={book.coverImage}
              alt={book.title}
              className="w-full h-full object-cover"
            />
          </div>
        </div>
        <div className="flex-1">
          <h1 className="text-3xl md:text-4xl font-bold text-white">
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

          <div className="flex gap-6 mt-4 text-xs text-white/40">
            <span>Originally in {book.originalLanguage}</span>
            <span>{book.originalTitle}</span>
            <span>{book.originalYear}</span>
          </div>

          <div className="flex gap-6 mt-2 text-xs text-white/40">
            <span>{book.totalChapters} chapters</span>
            <span>{Math.round(book.wordCount / 1000)}k words</span>
          </div>

          <div className="mt-6">
            <ReadButton bookId={book.id} accentColor={book.accentColor} />
          </div>
        </div>
      </div>

      {/* Summary */}
      <section className="mt-16">
        <h2 className="text-xl font-bold text-white mb-4">About This Book</h2>
        <p className="text-white/60 leading-relaxed max-w-3xl">
          {book.summary}
        </p>
      </section>

      {/* About the Author */}
      <section className="mt-16">
        <h2 className="text-xl font-bold text-white mb-4">
          About the Author
        </h2>
        <div className="flex gap-6 items-start">
          <Link href={`/authors/${author.id}`} className="flex-shrink-0">
            <div className="w-20 h-20 rounded-full overflow-hidden">
              <img
                src={author.image}
                alt={author.name}
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

      {/* Preview */}
      <section className="mt-16">
        <h2 className="text-xl font-bold text-white mb-4">Preview</h2>
        <div className="relative max-w-3xl">
          <p
            className="text-white/50 leading-relaxed"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            {book.previewText}
          </p>
          <div className="absolute bottom-0 left-0 right-0 h-24 bg-gradient-to-t from-[#0a0a0a] to-transparent" />
        </div>
        <div className="mt-6">
          <ReadButton bookId={book.id} accentColor={book.accentColor} />
        </div>
      </section>

      {/* Other Books */}
      {otherBooks.length > 0 && (
        <section className="mt-16">
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
