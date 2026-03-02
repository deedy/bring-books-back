import type { Metadata } from "next";
import { getCatalog } from "@/lib/data";
import ReaderLoader from "@/components/reader/ReaderLoader";

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
  const title = `Read ${book.title} by ${author?.name ?? "Unknown"}`;
  const description = `Read ${book.title} by ${author?.name ?? "Unknown"} — free English translation with illustrations`;
  const coverPng = book.coverImage.replace(".webp", ".png");
  return {
    title,
    description,
    openGraph: {
      title,
      description,
      images: [{ url: coverPng }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [coverPng],
    },
  };
}

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.books.filter((b) => b.type !== "anthology").map((book) => ({ id: book.id }));
}

export default async function ReadPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ReaderLoader bookId={id} />;
}
