import type { Metadata } from "next";
import Link from "next/link";
import { getCatalog } from "@/lib/data";
import BookCard from "@/components/BookCard";
import BackButton from "@/components/BackButton";

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.authors.map((author) => ({ id: author.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const catalog = getCatalog();
  const author = catalog.authors.find((a) => a.id === id);
  if (!author) return {};
  const title = `${author.name} — Author`;
  const description = author.bio.split("\n\n")[0].slice(0, 155);
  const ogImage = `https://storage.googleapis.com/grandoldbooks-assets${author.image}`;
  return {
    title,
    description,
    alternates: { canonical: `/authors/${id}` },
    openGraph: { title: author.name, description, images: [{ url: ogImage }] },
    twitter: { card: "summary", title: author.name, description, images: [ogImage] },
  };
}

export default async function AuthorPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const catalog = getCatalog();
  const author = catalog.authors.find((a) => a.id === id)!;
  const books = catalog.books.filter((b) => b.authorId === author.id);
  const bioParagraphs = author.bio.split("\n\n");

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Person",
    name: author.name,
    image: `https://grandoldbooks.com${author.image}`,
    url: `https://grandoldbooks.com/authors/${author.id}`,
    description: bioParagraphs[0],
  };

  const breadcrumbLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: [
      { "@type": "ListItem", position: 1, name: "Home", item: "https://grandoldbooks.com/" },
      { "@type": "ListItem", position: 2, name: author.name, item: `https://grandoldbooks.com/authors/${author.id}` },
    ],
  };

  return (
    <div className="max-w-4xl mx-auto px-6 pb-12">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(breadcrumbLd) }}
      />
      {/* Back bar */}
      <div className="sticky top-16 z-10 -mx-6 px-6 py-2 bg-[#0a0a0b]/80 backdrop-blur-md">
        <BackButton />
      </div>

      {/* Author Header */}
      <div className="flex flex-col items-center text-center mt-8">
        <div className="w-32 h-32 rounded-full overflow-hidden shadow-xl">
          <img
            src={author.image}
            alt={author.name}
            loading="lazy"
            className="w-full h-full object-cover"
          />
        </div>
        <h1 className="text-3xl font-bold text-white mt-6">{author.name}</h1>
        <p className="text-sm text-white/40 mt-1">{author.years}</p>
      </div>

      {/* Bio */}
      <div className="mt-10 space-y-4 max-w-2xl mx-auto">
        {bioParagraphs.map((p, i) => (
          <p key={i} className="text-white/60 leading-relaxed">
            {p}
          </p>
        ))}
      </div>

      {/* Books */}
      <section className="mt-16">
        <h2 className="text-xl font-bold text-white mb-6">
          Books by {author.name}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          {books.map((book) => (
            <BookCard key={book.id} book={book} author={author} />
          ))}
        </div>
      </section>
    </div>
  );
}
