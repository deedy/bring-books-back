import Link from "next/link";
import { Author } from "@/lib/types";

interface AuthorCardProps {
  author: Author;
}

export default function AuthorCard({ author }: AuthorCardProps) {
  return (
    <Link
      href={`/authors/${author.id}`}
      className="group flex flex-col items-center"
    >
      <div className="w-24 h-24 rounded-full overflow-hidden shadow-lg transition-all duration-200 group-hover:scale-[1.05] group-hover:shadow-xl">
        <img
          src={author.image}
          alt={author.name}
          loading="lazy"
          className="w-full h-full object-cover"
        />
      </div>
      <p className="mt-3 text-sm font-medium text-white/80 text-center group-hover:text-white transition-colors">
        {author.name}
      </p>
    </Link>
  );
}
