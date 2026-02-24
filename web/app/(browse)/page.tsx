import Link from "next/link";
import { getCatalog } from "@/lib/data";
import BookCard from "@/components/BookCard";
import AuthorCard from "@/components/AuthorCard";

export default function HomePage() {
  const catalog = getCatalog();
  const featured = catalog.books[0];
  const featuredAuthor = catalog.authors.find(
    (a) => a.id === featured.authorId
  )!;

  return (
    <div>
      {/* Hero */}
      <section className="relative py-24 px-6 overflow-hidden">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            background: `radial-gradient(ellipse at 30% 50%, ${featured.accentColor}, transparent 70%)`,
          }}
        />
        <div className="relative max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-12">
          <div className="w-48 md:w-64 flex-shrink-0">
            <div className="aspect-[2/3] rounded-lg overflow-hidden shadow-2xl">
              <img
                src={featured.coverImage}
                alt={featured.title}
                className="w-full h-full object-cover"
              />
            </div>
          </div>
          <div className="text-center md:text-left">
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
              {featured.title}
            </h1>
            <p className="text-lg text-white/60 mt-2">{featured.subtitle}</p>
            <p className="text-sm text-white/40 mt-1">
              by {featuredAuthor.name}
            </p>
            <p className="text-sm text-white/50 mt-4 max-w-lg leading-relaxed">
              {featured.summary.slice(0, 200)}...
            </p>
            <Link
              href={`/read/${featured.id}`}
              className="inline-block mt-6 px-6 py-3 rounded-lg font-medium text-white transition-opacity hover:opacity-90"
              style={{ backgroundColor: featured.accentColor }}
            >
              Start Reading
            </Link>
          </div>
        </div>
      </section>

      {/* Our Books */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-white mb-8">Our Books</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {catalog.books.map((book) => {
            const author = catalog.authors.find(
              (a) => a.id === book.authorId
            )!;
            return <BookCard key={book.id} book={book} author={author} />;
          })}
        </div>
      </section>

      {/* The Authors */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-white mb-8">The Authors</h2>
        <div className="flex gap-12 justify-center flex-wrap">
          {catalog.authors.map((author) => (
            <AuthorCard key={author.id} author={author} />
          ))}
        </div>
      </section>
    </div>
  );
}
