import { getCatalog } from "@/lib/data";

const BASE = "https://grandoldbooks.com";

function escapeXml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function GET() {
  const catalog = getCatalog();
  const authorsById = new Map(catalog.authors.map((a) => [a.id, a]));

  const recentBooks = catalog.books
    .filter((b) => b.type !== "anthology" && !b.anthologyId)
    .sort((a, b) => (b.addedDate ?? "").localeCompare(a.addedDate ?? ""))
    .slice(0, 20);

  const items = recentBooks
    .map((book) => {
      const author = authorsById.get(book.authorId);
      const authorName = author?.name ?? "Unknown";
      const pubDate = book.addedDate
        ? new Date(book.addedDate).toUTCString()
        : "";
      return `    <item>
      <title>${escapeXml(book.title)}</title>
      <link>${BASE}/books/${book.id}</link>
      <description>${escapeXml(book.summary)}</description>
      <author>${escapeXml(authorName)}</author>${pubDate ? `\n      <pubDate>${pubDate}</pubDate>` : ""}
      <guid>${BASE}/books/${book.id}</guid>
    </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Grand Old Books</title>
    <link>${BASE}</link>
    <description>Classic literature from around the world, translated and illustrated</description>
    <language>en-us</language>
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: { "Content-Type": "application/xml" },
  });
}
