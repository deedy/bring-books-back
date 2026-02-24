import { getCatalog } from "@/lib/data";
import ReaderLoader from "@/components/reader/ReaderLoader";

export function generateStaticParams() {
  const catalog = getCatalog();
  return catalog.books.map((book) => ({ id: book.id }));
}

export default async function ReadPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <ReaderLoader bookId={id} />;
}
