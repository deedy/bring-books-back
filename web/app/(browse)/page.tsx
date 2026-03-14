import { getCatalog } from "@/lib/data";
import HomeHero from "@/components/HomeHero";

export const dynamic = "force-dynamic";

export default function HomePage() {
  const catalog = getCatalog();
  // Only show top-level books + anthologies on home (not anthology members)
  const topLevelBooks = catalog.books.filter((b) => !b.anthologyId);
  const randomSeed = Math.random();

  return (
    <div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            name: "Grand Old Books",
            url: "https://grandoldbooks.com",
            description: "The greatest books you've never read",
            mainEntity: {
              "@type": "ItemList",
              itemListElement: topLevelBooks.map((b, i) => ({
                "@type": "ListItem",
                position: i + 1,
                url: `https://grandoldbooks.com/books/${b.id}`,
              })),
            },
          }),
        }}
      />
      <HomeHero books={topLevelBooks} authors={catalog.authors} randomSeed={randomSeed} />
    </div>
  );
}
