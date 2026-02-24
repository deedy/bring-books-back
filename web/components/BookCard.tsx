import Link from "next/link";
import { Book, Author } from "@/lib/types";

interface BookCardProps {
  book: Book;
  author: Author;
}

export default function BookCard({ book, author }: BookCardProps) {
  return (
    <Link
      href={`/books/${book.id}`}
      className="group block"
    >
      <div className="relative aspect-[2/3] rounded-lg overflow-hidden shadow-lg transition-all duration-200 group-hover:scale-[1.03] group-hover:shadow-2xl">
        <img
          src={book.coverImage}
          alt={book.title}
          loading="lazy"
          className="w-full h-full object-cover"
        />
      </div>
      <div className="mt-3">
        <h3 className="text-sm font-semibold text-white truncate">
          {book.title}
        </h3>
        <p className="text-xs text-white/50 mt-0.5">{author.name}</p>
      </div>
    </Link>
  );
}
