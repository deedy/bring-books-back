import { getCatalog } from "@/lib/data";
import HomeHero from "@/components/HomeHero";
import AuthorCard from "@/components/AuthorCard";

export default function HomePage() {
  const catalog = getCatalog();

  return (
    <div>
      <HomeHero books={catalog.books} authors={catalog.authors} />

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
