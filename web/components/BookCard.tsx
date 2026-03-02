import Link from "next/link";
import { Book, Author } from "@/lib/types";
import { readingTime } from "@/lib/utils";
import OfflineBadge from "@/components/OfflineBadge";

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
        <OfflineBadge bookId={book.id} />
        <img
          src={book.coverImage}
          alt={book.title}
          loading="lazy"
          className="w-full h-full object-cover"
        />
      </div>
      <div className="mt-3">
        <h3 className="text-sm font-semibold text-white line-clamp-2 leading-snug">
          {book.title}
        </h3>
        <p className="text-xs text-white/50 mt-0.5">{author.name}</p>
        <p className="text-[11px] text-white/30 mt-0.5">
          {book.originalLanguage} &middot; {book.originalYear} &middot; {readingTime(book.wordCount)}
        </p>
      </div>
    </Link>
  );
}
