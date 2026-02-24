import { getCatalog } from "@/lib/data";
import BookCard from "@/components/BookCard";

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.authors.map((author) => ({ id: author.id }));
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

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      {/* Author Header */}
      <div className="flex flex-col items-center text-center">
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
