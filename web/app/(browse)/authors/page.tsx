import type { Metadata } from "next";
import Link from "next/link";
import { getCatalog } from "@/lib/data";

export const metadata: Metadata = {
  title: "Authors",
  description: "Browse all authors on Grand Old Books — classic literature from around the world.",
  alternates: { canonical: "/authors" },
};

export default function AuthorsPage() {
  const catalog = getCatalog();
  const authors = catalog.authors
    .filter((a) => a.name !== "Various")
    .sort((a, b) => a.name.localeCompare(b.name));

  const collectionLd = {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    name: "Authors — Grand Old Books",
    url: "https://grandoldbooks.com/authors",
    description: "Browse all authors on Grand Old Books",
    mainEntity: {
      "@type": "ItemList",
      itemListElement: authors.map((a, i) => ({
        "@type": "ListItem",
        position: i + 1,
        url: `https://grandoldbooks.com/authors/${a.id}`,
      })),
    },
  };

  return (
    <div className="max-w-5xl mx-auto px-6 pb-12">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(collectionLd) }}
      />
      <h1 className="text-3xl font-bold text-white mt-8 mb-8">Authors</h1>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-8">
        {authors.map((author) => {
          const bookCount = catalog.books.filter(
            (b) => b.authorId === author.id && !b.anthologyId
          ).length;
          return (
            <Link key={author.id} href={`/authors/${author.id}`} className="group text-center">
              <div className="w-24 h-24 mx-auto rounded-full overflow-hidden shadow-lg transition-transform group-hover:scale-105">
                <img
                  src={author.image}
                  alt={author.name}
                  loading="lazy"
                  className="w-full h-full object-cover"
                />
              </div>
              <h2 className="text-sm font-semibold text-white mt-3 group-hover:text-white/80 transition-colors">
                {author.name}
              </h2>
              <p className="text-xs text-white/40 mt-0.5">{author.years}</p>
              <p className="text-xs text-white/30 mt-0.5">
                {bookCount} {bookCount === 1 ? "book" : "books"}
              </p>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
