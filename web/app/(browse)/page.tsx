import { getCatalog } from "@/lib/data";
import HomeHero from "@/components/HomeHero";

export default function HomePage() {
  const catalog = getCatalog();
  // Only show top-level books + anthologies on home (not anthology members)
  const topLevelBooks = catalog.books.filter((b) => !b.anthologyId).reverse();

  return (
    <div>
      <HomeHero books={topLevelBooks} authors={catalog.authors} />
    </div>
  );
}
