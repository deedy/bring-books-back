import { getCatalog } from "@/lib/data";
import HomeHero from "@/components/HomeHero";
import AuthorCard from "@/components/AuthorCard";

const isProd = process.env.NODE_ENV === "production";

export default function HomePage() {
  const catalog = getCatalog();
  // Only show top-level books + anthologies on home (not anthology members)
  const topLevelBooks = catalog.books.filter((b) => !b.anthologyId && (!isProd || b.enabled !== false)).reverse();

  return (
    <div>
      <HomeHero books={topLevelBooks} authors={catalog.authors} />

      {/* The Authors */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-white mb-8">The Authors</h2>
        <div className="flex gap-12 justify-center flex-wrap">
          {catalog.authors.filter((a) => a.bookIds.some((bid) => catalog.books.some((b) => b.id === bid && (!isProd || b.enabled !== false)))).map((author) => (
            <AuthorCard key={author.id} author={author} />
          ))}
        </div>
      </section>
    </div>
  );
}
